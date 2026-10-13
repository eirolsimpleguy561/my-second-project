import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import websockets

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    quantity: int
    price: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = 'pending'

@dataclass
class Trade:
    trade_id: str
    symbol: str
    price: float
    quantity: int
    buyer_order_id: str
    seller_order_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: List[Dict] = []  # Buy orders (highest price first)
        self.asks: List[Dict] = []  # Sell orders (lowest price first)
        self.last_price: float = 100.0
        self.trades: List[Trade] = []
        self.lock = asyncio.Lock()
    
    async def add_order(self, order: Order) -> Optional[Trade]:
        async with self.lock:
            if order.order_type == 'market':
                return await self._process_market_order(order)
            else:
                return await self._process_limit_order(order)
    
    async def _process_market_order(self, order: Order) -> Optional[Trade]:
        """Process a market order immediately at best available price"""
        if order.side == 'buy':
            if not self.asks:
                order.status = 'pending'
                return None
            
            # Match with best ask
            ask = self.asks[0]
            match_quantity = min(order.quantity, ask['quantity'])
            trade_price = ask['price']
            
            trade = Trade(
                trade_id=f"T{int(time.time())}{random.randint(100,999)}",
                symbol=self.symbol,
                price=trade_price,
                quantity=match_quantity,
                buyer_order_id=order.order_id,
                seller_order_id=ask['order_id']
            )
            
            self.trades.append(trade)
            self.last_price = trade_price
            
            # Update ask quantity
            ask['quantity'] -= match_quantity
            if ask['quantity'] == 0:
                self.asks.pop(0)
            
            return trade
        
        else:  # sell market order
            if not self.bids:
                order.status = 'pending'
                return None
            
            # Match with best bid
            bid = self.bids[0]
            match_quantity = min(order.quantity, bid['quantity'])
            trade_price = bid['price']
            
            trade = Trade(
                trade_id=f"T{int(time.time())}{random.randint(100,999)}",
                symbol=self.symbol,
                price=trade_price,
                quantity=match_quantity,
                buyer_order_id=bid['order_id'],
                seller_order_id=order.order_id
            )
            
            self.trades.append(trade)
            self.last_price = trade_price
            
            bid['quantity'] -= match_quantity
            if bid['quantity'] == 0:
                self.bids.pop(0)
            
            return trade
    
    async def _process_limit_order(self, order: Order) -> Optional[Trade]:
        """Process a limit order, add to book if not immediately matched"""
        if order.side == 'buy':
            # Try to match with existing asks
            while self.asks and self.asks[0]['price'] <= order.price:
                ask = self.asks[0]
                match_quantity = min(order.quantity, ask['quantity'])
                
                trade = Trade(
                    trade_id=f"T{int(time.time())}{random.randint(100,999)}",
                    symbol=self.symbol,
                    price=ask['price'],
                    quantity=match_quantity,
                    buyer_order_id=order.order_id,
                    seller_order_id=ask['order_id']
                )
                
                self.trades.append(trade)
                self.last_price = ask['price']
                
                order.quantity -= match_quantity
                ask['quantity'] -= match_quantity
                
                if ask['quantity'] == 0:
                    self.asks.pop(0)
                
                if order.quantity == 0:
                    order.status = 'filled'
                    return trade
            
            # Add remaining quantity to book
            if order.quantity > 0:
                order.status = 'open'
                self.bids.append({
                    'order_id': order.order_id,
                    'price': order.price,
                    'quantity': order.quantity,
                    'timestamp': order.timestamp
                })
                self.bids.sort(key=lambda x: x['price'], reverse=True)
            
            return None
        
        else:  # sell limit order
            # Try to match with existing bids
            while self.bids and self.bids[0]['price'] >= order.price:
                bid = self.bids[0]
                match_quantity = min(order.quantity, bid['quantity'])
                
                trade = Trade(
                    trade_id=f"T{int(time.time())}{random.randint(100,999)}",
                    symbol=self.symbol,
                    price=bid['price'],
                    quantity=match_quantity,
                    buyer_order_id=bid['order_id'],
                    seller_order_id=order.order_id
                )
                
                self.trades.append(trade)
                self.last_price = bid['price']
                
                order.quantity -= match_quantity
                bid['quantity'] -= match_quantity
                
                if bid['quantity'] == 0:
                    self.bids.pop(0)
                
                if order.quantity == 0:
                    order.status = 'filled'
                    return trade
            
            # Add remaining quantity to book
            if order.quantity > 0:
                order.status = 'open'
                self.asks.append({
                    'order_id': order.order_id,
                    'price': order.price,
                    'quantity': order.quantity,
                    'timestamp': order.timestamp
                })
                self.asks.sort(key=lambda x: x['price'])
            
            return None
    
    def get_snapshot(self) -> dict:
        """Get current order book snapshot"""
        return {
            'symbol': self.symbol,
            'last_price': self.last_price,
            'bids': self.bids[:10],
            'asks': self.asks[:10],
            'bid_count': len(self.bids),
            'ask_count': len(self.asks),
            'recent_trades': [t.__dict__ for t in self.trades[-10:]]
        }

class TradingEngine:
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.accounts: Dict[str, Dict] = {}
        self.order_history: Dict[str, List[Order]] = defaultdict(list)
        self.clients: set = set()
        self.running = True
    
    def create_symbol(self, symbol: str, initial_price: float = 100.0):
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            self.order_books[symbol].last_price = initial_price
    
    def create_account(self, account_id: str, initial_balance: float = 10000.0):
        self.accounts[account_id] = {
            'balance': initial_balance,
            'positions': {},
            'total_pnl': 0.0
        }
    
    async def place_order(self, account_id: str, order: Order) -> Optional[Trade]:
        """Place an order and process it"""
        if account_id not in self.accounts:
            raise ValueError("Account not found")
        
        if order.symbol not in self.order_books:
            raise ValueError("Symbol not found")
        
        # Check sufficient balance/position
        account = self.accounts[account_id]
        if order.side == 'buy':
            required = order.quantity * (order.price or self.order_books[order.symbol].last_price)
            if account['balance'] < required:
                raise ValueError("Insufficient balance")
        
        order_book = self.order_books[order.symbol]
        trade = await order_book.add_order(order)
        
        # Update account if trade executed
        if trade:
            if order.side == 'buy':
                account['balance'] -= trade.price * trade.quantity
                account['positions'][order.symbol] = account['positions'].get(order.symbol, 0) + trade.quantity
            else:
                account['balance'] += trade.price * trade.quantity
                account['positions'][order.symbol] = account['positions'].get(order.symbol, 0) - trade.quantity
        
        self.order_history[account_id].append(order)
        
        # Broadcast price update
        await self.broadcast_price_update(order.symbol)
        
        return trade
    
    async def broadcast_price_update(self, symbol: str):
        """Broadcast price updates to all connected WebSocket clients"""
        if symbol in self.order_books:
            snapshot = self.order_books[symbol].get_snapshot()
            message = json.dumps({
                'type': 'price_update',
                'data': snapshot
            })
            
            for client in self.clients:
                try:
                    await client.send(message)
                except:
                    pass
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections for real-time updates"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'subscribe':
                    symbol = data['symbol']
                    if symbol in self.order_books:
                        snapshot = self.order_books[symbol].get_snapshot()
                        await websocket.send(json.dumps({
                            'type': 'snapshot',
                            'data': snapshot
                        }))
        except:
            pass
        finally:
            self.clients.remove(websocket)
    
    def get_account_summary(self, account_id: str) -> dict:
        """Get account summary including positions and P&L"""
        account = self.accounts[account_id]
        total_value = account['balance']
        
        positions = []
        for symbol, quantity in account['positions'].items():
            if quantity != 0:
                current_price = self.order_books[symbol].last_price
                value = quantity * current_price
                total_value += value
                positions.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'value': value
                })
        
        return {
            'account_id': account_id,
            'balance': account['balance'],
            'total_value': total_value,
            'positions': positions,
            'total_pnl': total_value - 10000.0  # Assuming initial balance of 10000
        }

async def price_simulator(engine: TradingEngine):
    """Simulate random price movements for all symbols"""
    while True:
        for symbol, order_book in engine.order_books.items():
            # Random walk
            change = random.uniform(-2.0, 2.0)
            new_price = max(0.01, order_book.last_price + change)
            order_book.last_price = new_price
            
            # Add some random orders to simulate market activity
            if random.random() < 0.3:
                side = 'buy' if random.random() < 0.5 else 'sell'
                quantity = random.randint(1, 100)
                price = new_price * (1 + random.uniform(-0.02, 0.02))
                
                order = Order(
                    order_id=f"SIM{int(time.time())}{random.randint(100,999)}",
                    symbol=symbol,
                    side=side,
                    order_type='limit',
                    quantity=quantity,
                    price=round(price, 2)
                )
                await order_book.add_order(order)
        
        await asyncio.sleep(0.5)

async def main():
    engine = TradingEngine()
    
    # Create symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    for symbol in symbols:
        engine.create_symbol(symbol, random.uniform(50, 500))
    
    # Create accounts
    engine.create_account('trader1', 100000.0)
    engine.create_account('trader2', 50000.0)
    
    # Start price simulator
    asyncio.create_task(price_simulator(engine))
    
    # Start WebSocket server
    start_server = websockets.serve(engine.handle_websocket, "localhost", 8765)
    
    print("=== Stock Market Simulator ===")
    print("WebSocket server running on ws://localhost:8765")
    print("Symbols:", symbols)
    
    await start_server
    
    # Keep running
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())