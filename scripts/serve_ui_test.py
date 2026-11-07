"""Serve a built site with only the rent attachment failing, for UI regression tests."""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

os.chdir(Path(sys.argv[1]).resolve())


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if "/_file/data/rents." in path:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"Rent data unavailable (test)")
            return
        if not Path("." + path).exists() and Path("." + path + ".html").exists():
            self.path = path + ".html"
        super().do_GET()

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
print(f"http://127.0.0.1:{server.server_address[1]}", flush=True)
server.serve_forever()
