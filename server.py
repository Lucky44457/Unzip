import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 10000))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"UBZIP bot is running")


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


def run_bot():
    import m   # this runs m.py (your bot with app.run())


if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    run_bot()
