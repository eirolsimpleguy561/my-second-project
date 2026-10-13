import hashlib
import json
import time
import requests
import threading
from datetime import datetime
from typing import List, Dict, Any

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()
    
    def compute_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.compute_hash()
        print(f"Block mined: {self.hash}")
        return self.hash
    
    def to_dict(self):
        return {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }
    
    @staticmethod
    def from_dict(data):
        block = Block(data['index'], data['transactions'], data['timestamp'], 
                      data['previous_hash'], data['nonce'])
        block.hash = data['hash']
        return block

class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = difficulty
        self.nodes = set()
        self.create_genesis_block()
    
    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_transaction(self, sender, recipient, amount):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        }
        self.pending_transactions.append(transaction)
        return self.get_latest_block().index + 1
    
    def mine_pending_transactions(self, miner_address):
        block = Block(len(self.chain), self.pending_transactions, time.time(), self.get_latest_block().hash)
        block.mine_block(self.difficulty)
        
        self.chain.append(block)
        self.pending_transactions = [{
            'sender': 'system',
            'recipient': miner_address,
            'amount': 1,
            'timestamp': time.time()
        }]
        
        return block.hash
    
    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx['sender'] == address:
                    balance -= tx['amount']
                if tx['recipient'] == address:
                    balance += tx['amount']
        return balance
    
    def is_chain_valid(self, chain=None):
        if chain is None:
            chain = self.chain
        
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            if current_block.hash != current_block.compute_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if current_block.hash[:self.difficulty] != '0' * self.difficulty:
                return False
        
        return True
    
    def add_node(self, address):
        self.nodes.add(address)
    
    def resolve_conflicts(self):
        longest_chain = None
        max_length = len(self.chain)
        
        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    data = response.json()
                    chain_data = data['chain']
                    chain = [Block.from_dict(b) for b in chain_data]
                    length = data['length']
                    
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain
            except:
                pass
        
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
    def to_dict(self):
        return {
            'chain': [b.to_dict() for b in self.chain],
            'pending_transactions': self.pending_transactions,
            'length': len(self.chain)
        }

def main():
    print("=== Blockchain Demo ===")
    blockchain = Blockchain(difficulty=4)
    
    # Add some sample transactions
    blockchain.add_transaction("Alice", "Bob", 50)
    blockchain.add_transaction("Bob", "Charlie", 25)
    
    print("\nMining block...")
    blockchain.mine_pending_transactions("Miner1")
    
    print(f"\nMiner1 balance: {blockchain.get_balance('Miner1')}")
    print(f"Alice balance: {blockchain.get_balance('Alice')}")
    
    print("\nAdding more transactions...")
    blockchain.add_transaction("Charlie", "Alice", 10)
    blockchain.mine_pending_transactions("Miner1")
    
    print(f"\nMiner1 balance: {blockchain.get_balance('Miner1')}")
    print(f"Alice balance: {blockchain.get_balance('Alice')}")
    print(f"Bob balance: {blockchain.get_balance('Bob')}")
    print(f"Charlie balance: {blockchain.get_balance('Charlie')}")
    
    print(f"\nBlockchain valid: {blockchain.is_chain_valid()}")
    
    # Display chain
    print("\nBlockchain:")
    for block in blockchain.chain:
        print(f"Block {block.index}: {block.hash[:10]}... | Nonce: {block.nonce}")

if __name__ == "__main__":
    main()
