"""Tiny static file server for the Stellar landing page.
Runs on port 8200 to avoid conflicts with other projects (services-website on 8100, ERP on 8000)."""

import http.server
import socketserver
import os

PORT = 8200
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Stellar landing running at http://localhost:{PORT}")
        httpd.serve_forever()
