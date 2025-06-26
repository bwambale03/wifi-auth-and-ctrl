from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class NoDogSplashSimulator(BaseHTTPRequestHandler):
    def do_GET(self):
        # Redirect to splash page
        self.send_response(302)
        self.send_header('Location', 'http://localhost:3000')
        self.send_header('X-Client-MAC', '00:1A:2B:3C:4D:5E')  # Mock MAC
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/payments/activate-code'):
            # Forward to Flask backend with X-Client-MAC
            import requests
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            headers = {'X-Client-MAC': '00:1A:2B:3C:4D:5E', 'Content-Type': 'application/json'}
            response = requests.post('http://localhost:5000/api/payments/activate-code', data=post_data, headers=headers)
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.content)

server = HTTPServer(('192.168.1.49', 8080), NoDogSplashSimulator)
print('Simulating NoDogSplash on http://192.168.1.49:8080...')
server.serve_forever()
