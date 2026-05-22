"""Static server for marketing.cyberstellarbd.com — port 8202"""
import http.server, socketserver, os
PORT = 8202
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=DIRECTORY, **kw)
    def end_headers(self): self.send_header("Cache-Control", "no-store"); super().end_headers()
if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), H) as httpd:
        print(f"marketing-landing running at http://localhost:{PORT}")
        httpd.serve_forever()
