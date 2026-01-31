import http.server
import socketserver
import json
import os
import sys

# Import local modules
from solver import HitAndBlowSolver

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')

# Initialize Solver (Global state for simplicity in single-user scenario)
solver = HitAndBlowSolver()

class HitAndBlowHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html for root
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
            return self.serve_file(os.path.join(WEB_DIR, 'index.html'))
        
        # API: Get AI Move
        if self.path == '/api/move':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Use 'suggest_move'
            guess = solver.suggest_move()
            
            # Format as string or list? Let's send list
            response = {"guess": guess}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        # Fallback to serving static files from WEB_DIR
        # This allows referencing other assets if added later
        file_path = os.path.join(WEB_DIR, self.path.lstrip('/'))
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return self.serve_file(file_path)
             
        self.send_error(404, "File not found")

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body)

        if self.path == '/api/reset':
            solver.reset()
            self.send_json({"status": "ok", "message": "Solver reset"})
            return

        if self.path == '/api/update':
            # Expects: {"guess": [1,2,3,4], "hit": 1, "blow": 1}
            try:
                guess = data.get('guess')
                hit = data.get('hit')
                blow = data.get('blow')
                
                if guess is None or hit is None or blow is None:
                    raise ValueError("Missing fields")

                solver.update(guess, hit, blow)
                self.send_json({"status": "ok", "candidates": len(solver.candidates)})
            except Exception as e:
                self.send_error(400, str(e))
            return

    def serve_file(self, path):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            if path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server():
    print(f"Starting server at http://localhost:{PORT}")
    print("Use Ctrl+C to stop")
    with socketserver.TCPServer(("", PORT), HitAndBlowHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run_server()
