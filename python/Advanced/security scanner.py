import requests
import re
import json
import time
from urllib.parse import urlparse, urljoin, parse_qs
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

@dataclass
class Vulnerability:
    name: str
    severity: str  # Critical, High, Medium, Low
    description: str
    url: str
    parameter: str = ""
    payload: str = ""
    evidence: str = ""
    remediation: str = ""

@dataclass
class ScanResult:
    url: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    scan_time: str = field(default_factory=lambda: datetime.now().isoformat())
    pages_scanned: int = 0
    forms_found: int = 0
    parameters_tested: int = 0

class SecurityScanner:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.result = ScanResult(url=target_url)
        self.visited_urls: Set[str] = set()
        self.forms: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SecurityScanner/1.0 (+http://example.com/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Common payloads for testing
        self.sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' AND 1=1--",
            "' OR '1'='1';",
            "1 AND 1=1",
            "1 AND 1=2",
            "' AND SLEEP(5)--",
            "' OR SLEEP(5)--",
        ]
        
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "'><script>alert('XSS')</script>",
            "<input onfocus=alert('XSS') autofocus>",
            "<body onload=alert('XSS')>",
            "<iframe src='javascript:alert(1)'>",
        ]
    
    def crawl(self, url: str, max_pages: int = 50):
        """Crawl the website to discover pages and forms"""
        if len(self.visited_urls) >= max_pages:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        print(f"Crawling: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return
            
            self.result.pages_scanned += 1
            
            # Check for forms
            forms = self._extract_forms(response.text, url)
            self.forms.extend(forms)
            self.result.forms_found += len(forms)
            
            # Check security headers
            self._check_security_headers(response.headers, url)
            
            # Extract links for crawling
            links = self._extract_links(response.text, url)
            for link in links[:10]:  # Limit crawling
                if link not in self.visited_urls:
                    self.crawl(link, max_pages)
                    
        except Exception as e:
            print(f"Error crawling {url}: {e}")
    
    def _extract_forms(self, html: str, base_url: str) -> List[Dict]:
        """Extract forms from HTML"""
        forms = []
        
        # Simple regex-based form extraction
        form_pattern = r'<form[^>]*>(.*?)</form>'
        for form_match in re.finditer(form_pattern, html, re.DOTALL | re.IGNORECASE):
            form_html = form_match.group(0)
            
            # Get form action
            action_match = re.search(r'action=["\']([^"\']+)["\']', form_html, re.IGNORECASE)
            action = action_match.group(1) if action_match else ''
            
            # Get form method
            method_match = re.search(r'method=["\']([^"\']+)["\']', form_html, re.IGNORECASE)
            method = method_match.group(1).upper() if method_match else 'GET'
            
            # Extract input fields
            inputs = []
            input_pattern = r'<input[^>]*>'
            for input_match in re.finditer(input_pattern, form_html, re.IGNORECASE):
                input_html = input_match.group(0)
                
                name_match = re.search(r'name=["\']([^"\']+)["\']', input_html, re.IGNORECASE)
                name = name_match.group(1) if name_match else ''
                
                type_match = re.search(r'type=["\']([^"\']+)["\']', input_html, re.IGNORECASE)
                input_type = type_match.group(1) if type_match else 'text'
                
                if name and name not in ['submit', 'button', 'reset']:
                    inputs.append({'name': name, 'type': input_type, 'value': ''})
            
            if inputs:
                form_url = urljoin(base_url, action)
                forms.append({
                    'url': form_url,
                    'method': method,
                    'inputs': inputs,
                    'html': form_html
                })
        
        return forms
    
    def _extract_links(self, html: str, base_url: str) -> Set[str]:
        """Extract links from HTML"""
        links = set()
        
        # Extract href links
        link_pattern = r'href=["\']([^"\']+)["\']'
        for match in re.finditer(link_pattern, html, re.IGNORECASE):
            link = match.group(1)
            if link.startswith('http') or link.startswith('/'):
                full_url = urljoin(base_url, link)
                # Only keep links from the same domain
                if urlparse(full_url).netloc == urlparse(self.target_url).netloc:
                    links.add(full_url)
        
        return links
    
    def _check_security_headers(self, headers: Dict, url: str):
        """Check security headers"""
        security_headers = {
            'X-Frame-Options': {
                'missing_severity': 'Medium',
                'description': 'Missing X-Frame-Options header. This can lead to clickjacking attacks.',
                'remediation': 'Add X-Frame-Options: DENY or SAMEORIGIN'
            },
            'X-Content-Type-Options': {
                'missing_severity': 'Medium',
                'description': 'Missing X-Content-Type-Options header. This can lead to MIME type sniffing attacks.',
                'remediation': 'Add X-Content-Type-Options: nosniff'
            },
            'Strict-Transport-Security': {
                'missing_severity': 'Low',
                'description': 'Missing HSTS header. This allows downgrade attacks.',
                'remediation': 'Add Strict-Transport-Security: max-age=31536000; includeSubDomains'
            },
            'Content-Security-Policy': {
                'missing_severity': 'Medium',
                'description': 'Missing Content-Security-Policy header. This allows XSS attacks.',
                'remediation': 'Add Content-Security-Policy header with appropriate directives'
            },
            'Referrer-Policy': {
                'missing_severity': 'Low',
                'description': 'Missing Referrer-Policy header. This can leak information.',
                'remediation': 'Add Referrer-Policy: no-referrer-when-downgrade'
            }
        }
        
        for header, info in security_headers.items():
            if header not in headers:
                vuln = Vulnerability(
                    name=f'Missing {header} Header',
                    severity=info['missing_severity'],
                    description=info['description'],
                    url=url,
                    remediation=info['remediation']
                )
                self.result.vulnerabilities.append(vuln)
    
    def test_sql_injection(self, url: str, params: Dict):
        """Test for SQL injection vulnerabilities"""
        for param, value in params.items():
            for payload in self.sql_payloads:
                test_params = params.copy()
                test_params[param] = payload
                
                try:
                    response = self.session.get(url, params=test_params, timeout=5)
                    self.result.parameters_tested += 1
                    
                    # Check for SQL error messages
                    error_patterns = [
                        r'sql', r'database', r'error', r'warning',
                        r'mysql', r'postgresql', r'oracle', r'syntax',
                        r'select', r'from', r'where', r'union'
                    ]
                    
                    text_lower = response.text.lower()
                    for pattern in error_patterns:
                        if pattern in text_lower:
                            vuln = Vulnerability(
                                name='SQL Injection',
                                severity='Critical',
                                description=f'SQL injection vulnerability detected in parameter: {param}',
                                url=url,
                                parameter=param,
                                payload=payload,
                                evidence=f'Database error pattern detected: {pattern}',
                                remediation='Use parameterized queries and input validation'
                            )
                            self.result.vulnerabilities.append(vuln)
                            break
                    
                    # Check for time-based injection
                    if 'SLEEP' in payload:
                        start_time = time.time()
                        response = self.session.get(url, params=test_params, timeout=10)
                        elapsed = time.time() - start_time
                        if elapsed > 4:  # Significant delay
                            vuln = Vulnerability(
                                name='Time-based SQL Injection',
                                severity='High',
                                description=f'Time-based SQL injection detected in parameter: {param}',
                                url=url,
                                parameter=param,
                                payload=payload,
                                evidence=f'Response time: {elapsed:.2f} seconds',
                                remediation='Use parameterized queries and input validation'
                            )
                            self.result.vulnerabilities.append(vuln)
                            
                except Exception:
                    pass
    
    def test_xss(self, url: str, params: Dict):
        """Test for XSS vulnerabilities"""
        for param, value in params.items():
            for payload in self.xss_payloads:
                test_params = params.copy()
                test_params[param] = payload
                
                try:
                    response = self.session.get(url, params=test_params, timeout=5)
                    self.result.parameters_tested += 1
                    
                    # Check if payload is reflected in response
                    if payload in response.text:
                        # Check if it's actually executed (look for script/alert patterns)
                        if '<script>' in payload or 'alert' in payload:
                            vuln = Vulnerability(
                                name='Cross-Site Scripting (XSS)',
                                severity='High',
                                description=f'XSS vulnerability detected in parameter: {param}',
                                url=url,
                                parameter=param,
                                payload=payload,
                                evidence=f'Payload reflected in response: {payload[:50]}...',
                                remediation='Use proper output encoding and input validation'
                            )
                            self.result.vulnerabilities.append(vuln)
                            break
                except Exception:
                    pass
    
    def test_csrf(self, url: str):
        """Test for CSRF vulnerabilities"""
        # Check if forms have CSRF tokens
        for form in self.forms:
            if form['url'] == url:
                has_csrf_token = False
                for input_field in form['inputs']:
                    if 'csrf' in input_field['name'].lower() or 'token' in input_field['name'].lower():
                        has_csrf_token = True
                        break
                
                if not has_csrf_token and form['method'] == 'POST':
                    vuln = Vulnerability(
                        name='Missing CSRF Protection',
                        severity='High',
                        description='Form has no CSRF token. This allows cross-site request forgery attacks.',
                        url=url,
                        remediation='Add CSRF tokens to all state-changing forms'
                    )
                    self.result.vulnerabilities.append(vuln)
    
    def scan(self):
        """Run the full security scan"""
        print(f"Starting security scan of {self.target_url}")
        
        # Crawl the website
        self.crawl(self.target_url)
        
        print(f"Found {self.result.pages_scanned} pages and {self.result.forms_found} forms")
        
        # Test each page for vulnerabilities
        print("Testing for vulnerabilities...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            for url in self.visited_urls:
                # Extract parameters from URL
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                
                # Convert params to simple dict
                simple_params = {k: v[0] for k, v in params.items()}
                
                # Test SQL injection
                if simple_params:
                    executor.submit(self.test_sql_injection, url, simple_params)
                    executor.submit(self.test_xss, url, simple_params)
                
                # Test CSRF
                executor.submit(self.test_csrf, url)
        
        self.result.scan_time = datetime.now().isoformat()
        
        print(f"Scan complete. Found {len(self.result.vulnerabilities)} vulnerabilities.")
        
        return self.result
    
    def generate_report(self) -> str:
        """Generate a detailed security scan report"""
        report = []
        report.append("=" * 80)
        report.append("SECURITY SCAN REPORT")
        report.append("=" * 80)
        report.append(f"Target URL: {self.result.url}")
        report.append(f"Scan Time: {self.result.scan_time}")
        report.append(f"Pages Scanned: {self.result.pages_scanned}")
        report.append(f"Forms Found: {self.result.forms_found}")
        report.append(f"Parameters Tested: {self.result.parameters_tested}")
        report.append(f"Vulnerabilities Found: {len(self.result.vulnerabilities)}")
        report.append("")
        
        if self.result.vulnerabilities:
            # Group by severity
            by_severity = {'Critical': [], 'High': [], 'Medium': [], 'Low': []}
            for vuln in self.result.vulnerabilities:
                by_severity[vuln.severity].append(vuln)
            
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                vulns = by_severity.get(severity, [])
                if vulns:
                    report.append(f"\n{severity.upper()} ({len(vulns)})")
                    report.append("-" * 40)
                    for vuln in vulns:
                        report.append(f"  [{vuln.name}]")
                        report.append(f"  Description: {vuln.description}")
                        if vuln.parameter:
                            report.append(f"  Parameter: {vuln.parameter}")
                        if vuln.payload:
                            report.append(f"  Payload: {vuln.payload}")
                        if vuln.evidence:
                            report.append(f"  Evidence: {vuln.evidence}")
                        if vuln.remediation:
                            report.append(f"  Remediation: {vuln.remediation}")
                        report.append(f"  URL: {vuln.url}")
                        report.append("")
        else:
            report.append("No vulnerabilities found!")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)

async def main():
    print("=== Security Scanner ===")
    
    target = input("Enter target URL (e.g., http://testphp.vulnweb.com): ").strip()
    if not target:
        target = "http://testphp.vulnweb.com"
    
    scanner = SecurityScanner(target)
    result = scanner.scan()
    
    # Generate report
    report = scanner.generate_report()
    print("\n" + report)
    
    # Save report
    report_file = f"scan_report_{int(time.time())}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {report_file}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

# Install: pip install requests