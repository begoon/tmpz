import functions_framework
import json
import pathlib
import socket
import time
import flask

def tcp_probe(host, port, timeout=3) -> str:
    try:
        started = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        elapsed = time.time() - started
        return f'{elapsed:.3f}s'
    except Exception as e:
        return f'error connecting to "{host}:{port}": {e}'

@functions_framework.http
def handler(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    licence = json.loads(pathlib.Path("/secrets/ROC_LIC").read_text())
    signature = licence["license"]["signature"]
    licence["license"]["signature"] = signature[:4] + "..." + signature[-4:]

    server = licence["license"]["userdata"]["license_server"]
    host = server["hostname"]
    port = server["port"]
    timeout = server["timeout"]
    status = tcp_probe(host, port, timeout)
    licence["latency"] = status
    
    if request.path == "/z":
        info = [
            "host: " + host, 
            "latency: " + status, 
            "version: " + licence["license"]["version"], 
            "expiry: " + licence["license"]["expiry"],
            "signature: " + licence["license"]["signature"]
        ]
        response = flask.Response("\n".join(info) + "\n")
        response.headers['Content-Type'] = 'text/plain'
        return response
    return json.dumps(licence)
