import http.server
import socketserver
import os
import sys

DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flutter_client", "build", "web")

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

def run(port=8080):
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), NoCacheHTTPRequestHandler) as httpd:
        print(f"Serving Flutter Web without cache on http://127.0.0.1:{port} from {DIRECTORY}")
        sys.stdout.flush()
        httpd.serve_forever()

if __name__ == "__main__":
    run()
