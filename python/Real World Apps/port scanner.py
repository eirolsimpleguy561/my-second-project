import socket
import threading
from datetime import datetime

class PortScanner:
    def __init__(self, target, start_port=1, end_port=1024, max_threads=100):
        self.target = self.resolve_target(target)
        self.start_port = start_port
        self.end_port = end_port
        self.max_threads = max_threads
        self.open_ports = []
        self.lock = threading.Lock()
    
    def resolve_target(self, target):
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            print(f"Cannot resolve hostname: {target}")
            return None
    
    def get_service_name(self, port):
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
            443: "HTTPS", 3306: "MySQL", 3389: "RDP",
            5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB"
        }
        return services.get(port, "Unknown")
    
    def grab_banner(self, ip, port, timeout=3):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            sock.send(b"HELP\r\n")
            banner = sock.recv(1024).decode().strip()
            sock.close()
            return banner[:200] if banner else "No banner"
        except:
            return "No banner"
    
    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.target, port))
            
            if result == 0:
                service = self.get_service_name(port)
                banner = self.grab_banner(self.target, port) if port in [21,22,25,80,443] else "-"
                with self.lock:
                    self.open_ports.append((port, service, banner))
                    print(f"Port {port}: OPEN [{service}]")
            sock.close()
        except:
            pass
    
    def scan(self):
        if not self.target:
            return
        
        print(f"\n{'='*50}")
        print(f"Scanning target: {self.target}")
        print(f"Port range: {self.start_port}-{self.end_port}")
        print(f"Started at: {datetime.now()}")
        print(f"{'='*50}\n")
        
        threads = []
        for port in range(self.start_port, self.end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
            thread.start()
            
            if len(threads) >= self.max_threads:
                for t in threads:
                    t.join()
                threads = []
        
        for t in threads:
            t.join()
        
        print(f"\n{'='*50}")
        print(f"Scan completed at: {datetime.now()}")
        print(f"Open ports found: {len(self.open_ports)}")
        
        if self.open_ports:
            print("\nOpen Ports Summary:")
            print(f"{'Port':<8} {'Service':<12} {'Banner'}")
            print("-" * 50)
            for port, service, banner in sorted(self.open_ports):
                print(f"{port:<8} {service:<12} {banner[:50]}")

def main():
    print("=== Port Scanner ===")
    
    target = input("Enter target IP or hostname: ").strip()
    try:
        start_port = int(input("Start port (default 1): ") or 1)
        end_port = int(input("End port (default 1024): ") or 1024)
    except ValueError:
        start_port, end_port = 1, 1024
    
    scanner = PortScanner(target, start_port, end_port)
    scanner.scan()
    
    save = input("\nSave results to file? (y/n): ").lower()
    if save == 'y':
        filename = input("Filename: ").strip() or f"scan_{target}.txt"
        with open(filename, 'w') as f:
            f.write(f"Target: {target}\n")
            f.write(f"Open ports: {scanner.open_ports}\n")
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
