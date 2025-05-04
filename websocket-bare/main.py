import base64
import hashlib
import os
import pathlib
import socket
import ssl
import struct
from typing import Final


def create_websocket_key() -> str:
    return base64.b64encode(os.urandom(16)).decode()


def create_handshake_request(host: str, path: str, websocket_key: str) -> str:
    return (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {websocket_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )


WEBSOCKET_UUID: Final = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def validate_handshake_response(response: str, websocket_key: str) -> None:
    lines = response.split("\r\n")
    if not lines[0].startswith("HTTP/1.1 101"):
        raise Exception(f"invalid websocket handshake response: {lines}")

    accept = ""
    for line in lines:
        if line.lower().startswith("sec-websocket-accept:"):
            accept = line.split(":")[1].strip()

    expected = base64.b64encode(
        hashlib.sha1((websocket_key + WEBSOCKET_UUID).encode()).digest()
    ).decode()

    if accept != expected:
        raise Exception(f"Sec-WebSocket-Accept: {accept=} != {expected=}")


def encode_text_message(msg: str) -> bytes:
    payload = msg.encode()
    header = b"\x81"  # FIN=1, opcode=1 (text)
    length = len(payload)
    mask_bit = 0x80

    if length < 126:
        header += struct.pack("B", length | mask_bit)
    elif length < (1 << 16):
        header += struct.pack("!BH", 126 | mask_bit, length)
    else:
        header += struct.pack("!BQ", 127 | mask_bit, length)

    mask_key = os.urandom(4)
    masked_payload = bytearray(payload)
    for i in range(length):
        masked_payload[i] ^= mask_key[i % 4]

    return header + mask_key + masked_payload


def decode_text_message(data: bytes) -> str | None:
    b1, b2 = data[0], data[1]
    opcode = b1 & 0x0F

    if opcode == 0x8:
        raise Exception("connection closed by server")
    elif opcode != 0x1:
        return None  # ignore non-text frames

    masked = b2 & 0x80
    length = b2 & 0x7F
    idx = 2

    if length == 126:
        length = struct.unpack("!H", data[idx : idx + 2])[0]
        idx += 2
    elif length == 127:
        length = struct.unpack("!Q", data[idx : idx + 8])[0]
        idx += 8

    if masked:
        mask = data[idx : idx + 4]
        idx += 4
        payload = bytearray(data[idx : idx + length])
        for i in range(length):
            payload[i] ^= mask[i % 4]
        return payload.decode()
    return data[idx : idx + length].decode()


def websocket_client_ssl(host, port=443, path="/"):
    key = create_websocket_key()
    raw_sock = socket.create_connection((host, port))
    context = ssl.create_default_context()
    sock = context.wrap_socket(raw_sock, server_hostname=host)

    request = create_handshake_request(host, path, key)
    sock.send(request.encode())

    # read until end of HTTP headers
    raw = b""
    while b"\r\n\r\n" not in raw:
        raw += sock.recv(4096)
    response = raw.decode()

    validate_handshake_response(response, key)

    print("connected (wss) / type messages to send or Ctrl+C to exit")
    try:
        while True:
            msg = input("> ")
            if not msg:
                continue
            sock.send(encode_text_message(msg))
            data = sock.recv(4096)
            message = decode_text_message(data)
            if message is not None:
                print("received:", message)
    except KeyboardInterrupt:
        print("\nexiting")
    except Exception as e:
        print("error:", e)
    finally:
        sock.close()


env = dict(
    v.split("=")
    for v in (pathlib.Path(__file__).parent / ".env")
    .read_text()
    .strip()
    .split("\n")
)

HOST, PORT, PATH = env["HOST"], int(env["PORT"]), env["PATH"]

if __name__ == "__main__":
    websocket_client_ssl(HOST, PORT, PATH)
