import asyncio
import threading
import time
import json
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Tuple
import socket
import struct

# Try to import Scapy
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Scapy not installed. Install with: pip install scapy")

class TrafficAnalyzer:
    def __init__(self, interface: str = None):
        self.interface = interface
        self.running = False
        
        # Statistics storage
        self.packet_count = 0
        self.total_bytes = 0
        self.protocol_counts = defaultdict(int)
        self.top_connections = defaultdict(int)
        self.bandwidth_history = deque(maxlen=60)
        self.last_second = defaultdict(int)
        self.last_reset = time.time()
        
        # Connection tracking
        self.active_connections = {}
        self.connection_history = deque(maxlen=1000)
        
        # HTTP analysis
        self.http_requests = deque(maxlen=100)
        self.http_responses = deque(maxlen=100)
        
        # Alerts
        self.alerts = deque(maxlen=100)
        self.suspicious_patterns = [
            (b'payload', 'Suspicious payload'),
            (b'<script>', 'XSS attempt'),
            (b'select.*from', 'SQL injection attempt'),
        ]
        
        self.lock = threading.Lock()
        self.callbacks = []
    
    def _packet_handler(self, packet):
        """Handle captured packet"""
        if not self.running:
            return
        
        with self.lock:
            self.packet_count += 1
            
            # Get IP layer
            if packet.haslayer(IP):
                ip = packet[IP]
                src = ip.src
                dst = ip.dst
                size = len(packet)
                self.total_bytes += size
                
                # Update bandwidth
                self.last_second[size] += size
                
                # Protocol detection
                protocol = 'Unknown'
                if packet.haslayer(TCP):
                    protocol = 'TCP'
                    tcp = packet[TCP]
                    sport = tcp.sport
                    dport = tcp.dport
                    
                    # Connection tracking
                    conn_key = f"{src}:{sport} -> {dst}:{dport}"
                    if conn_key not in self.active_connections:
                        self.active_connections[conn_key] = {
                            'src': src,
                            'dst': dst,
                            'sport': sport,
                            'dport': dport,
                            'start': time.time(),
                            'packets': 0,
                            'bytes': 0
                        }
                    self.active_connections[conn_key]['packets'] += 1
                    self.active_connections[conn_key]['bytes'] += size
                    
                    # Check for HTTP
                    if packet.haslayer(Raw):
                        payload = packet[Raw].load
                        try:
                            data = payload.decode('utf-8', errors='ignore')
                            if 'GET ' in data or 'POST ' in data:
                                self._analyze_http_request(data, src, dst)
                        except:
                            pass
                    
                elif packet.haslayer(UDP):
                    protocol = 'UDP'
                elif packet.haslayer(ICMP):
                    protocol = 'ICMP'
                
                self.protocol_counts[protocol] += 1
                
                # Check for suspicious patterns
                if packet.haslayer(Raw):
                    payload = packet[Raw].load
                    for pattern, alert_msg in self.suspicious_patterns:
                        if isinstance(pattern, str):
                            pattern = pattern.encode()
                        if pattern in payload:
                            self.alerts.append({
                                'time': time.time(),
                                'message': alert_msg,
                                'src': src,
                                'dst': dst,
                                'protocol': protocol
                            })
        
        # Call external callbacks
        for callback in self.callbacks:
            try:
                callback(packet)
            except:
                pass
    
    def _analyze_http_request(self, data: str, src: str, dst: str):
        """Analyze HTTP request"""
        lines = data.split('\r\n')
        if lines:
            request_line = lines[0].split(' ')
            if len(request_line) >= 2:
                method = request_line[0]
                path = request_line[1]
                
                # Parse headers
                headers = {}
                for line in lines[1:]:
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        headers[key] = value
                
                self.http_requests.append({
                    'time': time.time(),
                    'method': method,
                    'path': path,
                    'headers': headers,
                    'src': src,
                    'dst': dst
                })
    
    def start(self):
        """Start packet capture"""
        if not SCAPY_AVAILABLE:
            print("Scapy is required for packet capture")
            return
        
        self.running = True
        print(f"Starting packet capture on interface: {self.interface or 'default'}")
        
        # Start statistics collector
        threading.Thread(target=self._collect_stats, daemon=True).start()
        
        # Start packet capture
        sniff(iface=self.interface, prn=self._packet_handler, store=False)
    
    def stop(self):
        """Stop packet capture"""
        self.running = False
        print("Packet capture stopped")
    
    def _collect_stats(self):
        """Collect and update statistics periodically"""
        while self.running:
            time.sleep(1)
            
            with self.lock:
                total = sum(self.last_second.values())
                self.bandwidth_history.append(total)
                self.last_second.clear()
                
                # Update connection tracking
                current_time = time.time()
                for conn_key in list(self.active_connections.keys()):
                    conn = self.active_connections[conn_key]
                    if current_time - conn['start'] > 300:  # 5 minute timeout
                        self.connection_history.append(conn)
                        del self.active_connections[conn_key]
    
    def get_stats(self) -> dict:
        """Get current traffic statistics"""
        with self.lock:
            return {
                'packets': self.packet_count,
                'total_bytes': self.total_bytes,
                'bandwidth_mbps': sum(self.bandwidth_history) * 8 / 1_000_000 if self.bandwidth_history else 0,
                'protocols': dict(self.protocol_counts),
                'active_connections': len(self.active_connections),
                'alerts': len(self.alerts),
                'http_requests': len(self.http_requests)
            }
    
    def get_top_connections(self, n: int = 10) -> List[Tuple[str, int]]:
        """Get top connections by packet count"""
        with self.lock:
            conn_counts = {}
            for conn in self.active_connections.values():
                key = f"{conn['src']} -> {conn['dst']}"
                conn_counts[key] = conn['packets']
            
            for conn in self.connection_history:
                key = f"{conn['src']} -> {conn['dst']}"
                conn_counts[key] = conn['packets']
            
            return sorted(conn_counts.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_protocol_distribution(self) -> Dict[str, float]:
        """Get protocol distribution as percentages"""
        with self.lock:
            total = sum(self.protocol_counts.values())
            if total == 0:
                return {}
            
            return {proto: (count / total) * 100 for proto, count in self.protocol_counts.items()}
    
    def get_alerts(self) -> List[Dict]:
        """Get recent security alerts"""
        with self.lock:
            return list(self.alerts)
    
    def register_callback(self, callback):
        """Register callback for packet processing"""
        self.callbacks.append(callback)

class WebInterface:
    """Simple web interface for monitoring"""
    def __init__(self, analyzer: TrafficAnalyzer, port: int = 8080):
        self.analyzer = analyzer
        self.port = port
    
    async def handle_request(self, request):
        """Handle HTTP requests"""
        if request.path == '/':
            return self._render_dashboard()
        elif request.path == '/stats':
            return json.dumps(self.analyzer.get_stats())
        elif request.path == '/connections':
            return json.dumps(self.analyzer.get_top_connections())
        elif request.path == '/alerts':
            return json.dumps(self.analyzer.get_alerts())
        else:
            return 'Not found'
    
    def _render_dashboard(self) -> str:
        """Render HTML dashboard"""
        stats = self.analyzer.get_stats()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Traffic Analyzer</title>
            <style>
                body { font-family: Arial; margin: 20px; background: #f0f2f5; }
                .dashboard { max-width: 1200px; margin: 0 auto; }
                .card { background: white; border-radius: 8px; padding: 20px; margin: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-block; }
                .card h3 { margin: 0 0 10px 0; color: #666; }
                .card .value { font-size: 28px; font-weight: bold; color: #333; }
                .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 5px 0; }
                .alert.critical { background: #f8d7da; border-left-color: #dc3545; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
                .chart-container { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
                .alert-badge { background: #dc3545; color: white; border-radius: 12px; padding: 2px 8px; font-size: 12px; }
            </style>
            <script>
                async function updateStats() {
                    try {
                        const response = await fetch('/stats');
                        const data = await response.json();
                        document.getElementById('packets').textContent = data.packets;
                        document.getElementById('bytes').textContent = (data.total_bytes / 1024 / 1024).toFixed(2) + ' MB';
                        document.getElementById('bandwidth').textContent = data.bandwidth_mbps.toFixed(2) + ' Mbps';
                        document.getElementById('connections').textContent = data.active_connections;
                        document.getElementById('alerts').textContent = data.alerts;
                        document.getElementById('requests').textContent = data.http_requests;
                    } catch(e) {}
                    
                    try {
                        const response = await fetch('/alerts');
                        const alerts = await response.json();
                        const container = document.getElementById('alerts-container');
                        container.innerHTML = alerts.map(a => 
                            `<div class="alert">
                                <strong>${a.message}</strong><br>
                                ${a.src} -> ${a.dst} (${a.protocol})
                            </div>`
                        ).join('') || 'No alerts';
                    } catch(e) {}
                }
                
                setInterval(updateStats, 2000);
                updateStats();
            </script>
        </head>
        <body>
            <div class="dashboard">
                <h1>Network Traffic Analyzer</h1>
                
                <div class="grid">
                    <div class="card">
                        <h3>Packets</h3>
                        <div class="value" id="packets">0</div>
                    </div>
                    <div class="card">
                        <h3>Total Data</h3>
                        <div class="value" id="bytes">0 MB</div>
                    </div>
                    <div class="card">
                        <h3>Bandwidth</h3>
                        <div class="value" id="bandwidth">0 Mbps</div>
                    </div>
                    <div class="card">
                        <h3>Active Connections</h3>
                        <div class="value" id="connections">0</div>
                    </div>
                    <div class="card">
                        <h3>Alerts</h3>
                        <div class="value" id="alerts">0</div>
                    </div>
                    <div class="card">
                        <h3>HTTP Requests</h3>
                        <div class="value" id="requests">0</div>
                    </div>
                </div>
                
                <div class="card" style="width: 100%;">
                    <h3>Security Alerts</h3>
                    <div id="alerts-container">No alerts</div>
                </div>
                
                <div class="card" style="width: 100%;">
                    <h3>Protocol Distribution</h3>
                    <div>
                        """ + f"{stats.get('protocols', {})}" + """
                    </div>
                </div>
                
                <div class="card" style="width: 100%;">
                    <h3>Instructions</h3>
                    <p>Run the analyzer with:</p>
                    <code>python analyzer.py --interface eth0</code>
                    <p>Or specify no interface to scan all available.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

async def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Traffic Analyzer')
    parser.add_argument('--interface', '-i', help='Network interface to sniff')
    parser.add_argument('--web', '-w', action='store_true', help='Start web interface')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Web interface port')
    
    args = parser.parse_args()
    
    if not SCAPY_AVAILABLE:
        print("Scapy is required. Install with: pip install scapy")
        sys.exit(1)
    
    print("=== Network Traffic Analyzer ===")
    
    analyzer = TrafficAnalyzer(args.interface)
    
    if args.web:
        try:
            from aiohttp import web
            
            web_interface = WebInterface(analyzer, args.port)
            app = web.Application()
            app.router.add_get('/', lambda r: web.Response(text=web_interface._render_dashboard(), content_type='text/html'))
            app.router.add_get('/stats', lambda r: web.json_response(analyzer.get_stats()))
            app.router.add_get('/connections', lambda r: web.json_response(analyzer.get_top_connections()))
            app.router.add_get('/alerts', lambda r: web.json_response(analyzer.get_alerts()))
            
            print(f"Web interface running at http://localhost:{args.port}")
            print("Press Ctrl+C to stop")
            
            # Start analyzer in thread
            import threading
            thread = threading.Thread(target=analyzer.start, daemon=True)
            thread.start()
            
            # Start web server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', args.port)
            await site.start()
            
            await asyncio.Future()
        except ImportError:
            print("aiohttp not installed. Install with: pip install aiohttp")
            analyzer.start()
    else:
        analyzer.start()

if __name__ == "__main__":
    asyncio.run(main())

# Install: pip install scapy aiohttp
# Run with: python analyzer.py -i eth0 -w