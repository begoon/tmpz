import http
import http.server
import logging
from urllib.parse import parse_qs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info(self.path)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        query = parse_qs(self.path.split("?")[1])
        logging.info(query)
        self.wfile.write(b"ha?")
        logging.info(self.request)

class Server(http.server.HTTPServer):
    def __init__(self, host, port):
        super().__init__((host, port), Handler)



def main():
    server = Server("localhost", 8000)
    server.handle_request()

if __name__ == "__main__":
    main()
