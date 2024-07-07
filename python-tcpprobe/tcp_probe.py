import socket
import sys
import time


def tcp_probe(host, port, timeout=3) -> str:
    try:
        started = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        elapsed = time.time() - started
        return f'responded in {elapsed:.3f} seconds'
    except Exception as e:
        return f'error connecting to "{host}:{port}": {e}'


host = sys.argv[1]
port = int(sys.argv[2])

if error := tcp_probe(host, port, timeout=3):
    print(error)
else:
    print("OK")
