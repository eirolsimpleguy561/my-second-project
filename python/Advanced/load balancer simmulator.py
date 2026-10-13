import threading
import time
import random
import socket
import sys
from collections import defaultdict

class BackendServer:
    def __init__(self, name, host='localhost', port=8000, weight=1):
        self.name = name
        self.host = host
        self.port = port
        self.weight = weight
        self.active_connections = 0
        self.total_requests = 0
        self.response_time = 0
        self.is_healthy = True
    
    def handle_request(self, request_id):
        self.active_connections += 1
        self.total_requests += 1
        start = time.time()
        time.sleep(random.uniform(0.01, 0.1))  # Simulate processing
        self.response_time = (self.response_time + (time.time() - start)) / 2
        self.active_connections -= 1
        return f"Response from {self.name}: Request {request_id}"

class LoadBalancer:
    def __init__(self, algorithm='round_robin'):
        self.servers = []
        self.algorithm = algorithm
        self.current_index = 0
        self.lock = threading.Lock()
        self.request_count = 0
    
    def add_server(self, server):
        self.servers.append(server)
        print(f"Added server: {server.name}")
    
    def remove_server(self, name):
        self.servers = [s for s in self.servers if s.name != name]
        print(f"Removed server: {name}")
    
    def get_server_round_robin(self):
        with self.lock:
            healthy_servers = [s for s in self.servers if s.is_healthy]
            if not healthy_servers:
                return None
            self.current_index = (self.current_index + 1) % len(healthy_servers)
            return healthy_servers[self.current_index]
    
    def get_server_least_connections(self):
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        return min(healthy_servers, key=lambda s: s.active_connections)
    
    def get_server_weighted(self):
        healthy_servers = [s for s in self.servers if s.is_healthy]
        if not healthy_servers:
            return None
        total_weight = sum(s.weight for s in healthy_servers)
        if total_weight == 0:
            return healthy_servers[0]
        
        random_value = random.randint(1, total_weight)
        cumulative = 0
        for server in healthy_servers:
            cumulative += server.weight
            if random_value <= cumulative:
                return server
        return healthy_servers[0]
    
    def get_server(self):
        if self.algorithm == 'round_robin':
            return self.get_server_round_robin()
        elif self.algorithm == 'least_connections':
            return self.get_server_least_connections()
        elif self.algorithm == 'weighted':
            return self.get_server_weighted()
        return None
    
    def route_request(self, request_id):
        server = self.get_server()
        if server:
            self.request_count += 1
            return server.handle_request(request_id)
        return "No healthy servers available"
    
    def get_stats(self):
        stats = {
            'total_requests': self.request_count,
            'servers': []
        }
        for server in self.servers:
            stats['servers'].append({
                'name': server.name,
                'active': server.active_connections,
                'total': server.total_requests,
                'response_time': f"{server.response_time*1000:.2f}ms",
                'healthy': server.is_healthy
            })
        return stats

def health_check(lb):
    while True:
        for server in lb.servers:
            # Simulate health check
            server.is_healthy = random.random() > 0.1  # 90% uptime
        time.sleep(5)

def display_stats(lb):
    while True:
        time.sleep(2)
        stats = lb.get_stats()
        print(f"\n--- Load Balancer Stats (Algorithm: {lb.algorithm}) ---")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"{'Server':<15} {'Active':<8} {'Total':<10} {'Avg Response':<15} {'Health'}")
        for s in stats['servers']:
            status = '✓' if s['healthy'] else '✗'
            print(f"{s['name']:<15} {s['active']:<8} {s['total']:<10} {s['response_time']:<15} {status}")

def main():
    print("=== Load Balancer Simulator ===")
    
    algorithm = input("Algorithm (round_robin/least_connections/weighted): ").strip() or 'round_robin'
    lb = LoadBalancer(algorithm)
    
    num_servers = int(input("Number of backend servers: ") or 3)
    for i in range(num_servers):
        weight = int(input(f"Weight for server {i+1} (default 1): ") or 1)
        server = BackendServer(f"Server{i+1}", weight=weight)
        lb.add_server(server)
    
    # Start health check and stats display threads
    threading.Thread(target=health_check, args=(lb,), daemon=True).start()
    threading.Thread(target=display_stats, args=(lb,), daemon=True).start()
    
    print("\nLoad balancer running. Press Ctrl+C to stop.")
    request_id = 0
    
    try:
        while True:
            time.sleep(random.uniform(0.1, 0.5))  # Simulate incoming requests
            request_id += 1
            response = lb.route_request(request_id)
            if request_id % 10 == 0:
                print(f"[{request_id}] {response[:50]}...")
    except KeyboardInterrupt:
        print("\nShutting down...")
        final_stats = lb.get_stats()
        print(f"Final total requests: {final_stats['total_requests']}")

if __name__ == "__main__":
    main()
