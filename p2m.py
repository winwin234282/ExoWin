import os
import sys
import ssl
import socket
import threading
import http.server
import socketserver
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
LISTEN_HOST = '0.0.0.0'  # Listen on all interfaces
LISTEN_PORT = 12443  # HTTPS port
TARGET_HOST = '127.0.0.1'  # Flask app host
TARGET_PORT = 12000  # Flask app port
CERT_FILE = '/root/ExoWin/ssl/cert.pem'
KEY_FILE = '/root/ExoWin/ssl/private.key'

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request('GET')

    def do_POST(self):
        self.proxy_request('POST')

    def do_PUT(self):
        self.proxy_request('PUT')

    def do_DELETE(self):
        self.proxy_request('DELETE')

    def do_OPTIONS(self):
        self.proxy_request('OPTIONS')

    def proxy_request(self, method):
        url = f'http://{TARGET_HOST}:{TARGET_PORT}{self.path}'
        
        # Copy request headers
        headers = {}
        for header in self.headers:
            headers[header] = self.headers[header]
        
        # Get request body for POST/PUT
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            # Create request
            req = urllib.request.Request(
                url, 
                data=body,
                headers=headers,
                method=method
            )
            
            # Send request to target server
            with urllib.request.urlopen(req) as response:
                # Set response status code
                self.send_response(response.status)
                
                # Copy response headers
                for header in response.headers:
                    self.send_header(header, response.headers[header])
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())
            print(f'Error: {str(e)}')

def run_server():
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    # Create server
    httpd = HTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHTTPRequestHandler)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f'Starting HTTPS proxy server on {LISTEN_HOST}:{LISTEN_PORT}')
    print(f'Forwarding to HTTP server at {TARGET_HOST}:{TARGET_PORT}')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Server stopped')
    finally:
        httpd.server_close()

if __name__ == '__main__':
    # Check if running as root (required for port 443)
    if os.geteuid() != 0:
        print('Error: This script must be run as root to bind to port 443')
        sys.exit(1)
        
    # Check if certificate files exist
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f'Error: Certificate files not found at {CERT_FILE} and {KEY_FILE}')
        sys.exit(1)
        
    run_server()
