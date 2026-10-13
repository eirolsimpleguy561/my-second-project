import asyncio
import json
import random
import uuid
import time
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import websockets

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    ENDED = "ended"

@dataclass
class Player:
    id: str
    name: str
    websocket: any
    x: float = 0.0
    y: float = 0.0
    score: int = 0
    alive: bool = True
    last_update: float = field(default_factory=time.time)

@dataclass
class GameRoom:
    id: str
    name: str
    players: Dict[str, Player] = field(default_factory=dict)
    state: GameState = GameState.WAITING
    max_players: int = 4
    food: List[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'player_count': len(self.players),
            'max_players': self.max_players,
            'state': self.state.value,
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'x': p.x,
                    'y': p.y,
                    'score': p.score,
                    'alive': p.alive
                }
                for p in self.players.values()
            ],
            'food': self.food
        }

class GameServer:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.players: Dict[str, Player] = {}
        self.game_tick_rate = 1/60  # 60 FPS
        self.food_spawn_rate = 2.0  # Seconds between food spawns
        self.running = True
    
    async def create_room(self, room_name: str, max_players: int = 4) -> GameRoom:
        """Create a new game room"""
        room_id = str(uuid.uuid4())[:8]
        room = GameRoom(
            id=room_id,
            name=room_name,
            max_players=max_players
        )
        self.rooms[room_id] = room
        
        # Spawn initial food
        for _ in range(10):
            room.food.append(self._generate_food())
        
        return room
    
    def _generate_food(self) -> dict:
        """Generate food at random position"""
        return {
            'id': str(uuid.uuid4())[:6],
            'x': random.uniform(-400, 400),
            'y': random.uniform(-300, 300),
            'value': random.choice([1, 2, 3])
        }
    
    async def join_room(self, room_id: str, player_name: str, websocket) -> Optional[Player]:
        """Add a player to a room"""
        room = self.rooms.get(room_id)
        if not room:
            return None
        
        if len(room.players) >= room.max_players:
            return None
        
        # Check if player already in room (reconnect)
        for player in room.players.values():
            if player.name == player_name:
                player.websocket = websocket
                player.alive = True
                return player
        
        # Create new player
        player_id = str(uuid.uuid4())[:8]
        player = Player(
            id=player_id,
            name=player_name,
            websocket=websocket,
            x=random.uniform(-100, 100),
            y=random.uniform(-100, 100)
        )
        room.players[player_id] = player
        self.players[player_id] = player
        
        # Start game if enough players
        if len(room.players) >= 2 and room.state == GameState.WAITING:
            room.state = GameState.PLAYING
            await self.broadcast_to_room(room_id, {
                'type': 'game_started',
                'message': 'Game starting!'
            })
        
        return player
    
    async def leave_room(self, room_id: str, player_id: str):
        """Remove a player from a room"""
        room = self.rooms.get(room_id)
        if not room:
            return
        
        if player_id in room.players:
            player = room.players.pop(player_id)
            await player.websocket.close()
            del self.players[player_id]
            
            # End game if not enough players
            if len(room.players) < 2 and room.state == GameState.PLAYING:
                room.state = GameState.WAITING
                await self.broadcast_to_room(room_id, {
                    'type': 'game_ended',
                    'message': 'Not enough players'
                })
            
            # Clean up empty rooms
            if len(room.players) == 0:
                del self.rooms[room_id]
    
    async def update_player_position(self, room_id: str, player_id: str, x: float, y: float):
        """Update player position"""
        room = self.rooms.get(room_id)
        if not room:
            return
        
        player = room.players.get(player_id)
        if not player or not player.alive:
            return
        
        # Update position
        player.x = max(-400, min(400, x))
        player.y = max(-300, min(300, y))
        player.last_update = time.time()
    
    async def game_loop(self, room_id: str):
        """Main game loop for a room"""
        room = self.rooms.get(room_id)
        if not room:
            return
        
        while room.state == GameState.PLAYING and len(room.players) >= 2:
            start_time = time.time()
            
            # Update game state
            await self._update_game(room)
            
            # Broadcast state to all players
            await self.broadcast_to_room(room_id, {
                'type': 'game_state',
                'room': room.to_dict()
            })
            
            # Maintain fixed tick rate
            elapsed = time.time() - start_time
            await asyncio.max(0, self.game_tick_rate - elapsed)
        
        room.state = GameState.ENDED
    
    async def _update_game(self, room: GameRoom):
        """Update game physics and logic"""
        # Spawn food periodically
        if len(room.food) < 20 and random.random() < 0.3:
            room.food.append(self._generate_food())
        
        # Check for food collisions
        for player in room.players.values():
            if not player.alive:
                continue
            
            for food in room.food[:]:
                dx = player.x - food['x']
                dy = player.y - food['y']
                if dx*dx + dy*dy < 400:  # Within 20 units
                    player.score += food['value']
                    room.food.remove(food)
                    # Spawn replacement food
                    room.food.append(self._generate_food())
        
        # Check for player collisions (tag game)
        players_list = list(room.players.values())
        for i, p1 in enumerate(players_list):
            if not p1.alive:
                continue
            for p2 in players_list[i+1:]:
                if not p2.alive:
                    continue
                dx = p1.x - p2.x
                dy = p1.y - p2.y
                if dx*dx + dy*dy < 100:  # Within 10 units
                    # Randomly decide who gets tagged
                    if random.random() < 0.5:
                        p1.alive = False
                    else:
                        p2.alive = False
        
        # Respawn dead players after delay
        for player in room.players.values():
            if not player.alive and random.random() < 0.05:
                player.alive = True
                player.x = random.uniform(-400, 400)
                player.y = random.uniform(-300, 300)
    
    async def broadcast_to_room(self, room_id: str, message: dict):
        """Broadcast message to all players in a room"""
        room = self.rooms.get(room_id)
        if not room:
            return
        
        for player in room.players.values():
            try:
                await player.websocket.send(json.dumps(message))
            except:
                pass
    
    async def handle_connection(self, websocket, path):
        """Handle WebSocket connection"""
        try:
            # Receive initial join message
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] != 'join':
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'First message must be join'
                }))
                return
            
            room_id = data.get('room_id')
            player_name = data.get('name', 'Player')
            
            # Find or create room
            if not room_id or room_id not in self.rooms:
                room = await self.create_room(f"Room-{len(self.rooms)+1}")
                room_id = room.id
            
            # Join room
            player = await self.join_room(room_id, player_name, websocket)
            if not player:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Room is full'
                }))
                return
            
            # Send room state to new player
            room = self.rooms[room_id]
            await websocket.send(json.dumps({
                'type': 'join_success',
                'room': room.to_dict(),
                'player_id': player.id
            }))
            
            # Start game loop if not already running
            if room.state == GameState.PLAYING:
                asyncio.create_task(self.game_loop(room_id))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data['type'] == 'move':
                        await self.update_player_position(
                            room_id,
                            player.id,
                            data.get('x', 0),
                            data.get('y', 0)
                        )
                    elif data['type'] == 'chat':
                        await self.broadcast_to_room(room_id, {
                            'type': 'chat',
                            'player': player.name,
                            'message': data['message']
                        })
                except json.JSONDecodeError:
                    pass
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Handle disconnection
            if player:
                await self.leave_room(room_id, player.id)

async def main():
    server = GameServer()
    
    start_server = websockets.serve(server.handle_connection, "localhost", 8765)
    
    print("=== Multiplayer Game Server ===")
    print("WebSocket server running on ws://localhost:8765")
    print("\nTo connect, send join message:")
    print(json.dumps({'type': 'join', 'name': 'YourName'}, indent=2))
    
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

# Install: pip install websockets