import binascii  # type: ignore
import hashlib
import os
import socket
import ssl
import struct
import time  # type: ignore

import machine  # type: ignore
import network  # type: ignore
import urequests  # type: ignore
from machine import Pin, Timer  # type: ignore

import settings


def base64_encode(data: bytes) -> str:
    return binascii.b2a_base64(data, newline=False).decode()


def create_websocket_key():
    return base64_encode(os.urandom(16))


def create_handshake_request(host, path, websocket_key):
    return (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {websocket_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )


WS_UUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def validate_handshake_response(response: str, websocket_key: str) -> None:
    lines = response.split("\r\n")
    if not lines[0].startswith("HTTP/1.1 101"):
        raise Exception(f"invalid handshake response: {lines[0]}")

    accept = ""
    for line in lines:
        if line.lower().startswith("sec-websocket-accept:"):
            accept = line.split(":")[1].strip()

    expected = base64_encode(
        hashlib.sha1((websocket_key + WS_UUID).encode()).digest()
    )

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


def decode_text_message(data: bytes) -> str:
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


def websocket_client_ssl(host: str, port: int, path: str) -> None:
    key = create_websocket_key()
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    af = socket.getaddrinfo(host, 443)[0][-1]
    raw_sock.connect(af)
    sock = ssl.wrap_socket(raw_sock, server_hostname=host)

    request = create_handshake_request(host, path, key)
    sock.send(request.encode())

    # read until end of HTTP headers
    raw = b""
    while b"\r\n\r\n" not in raw:
        raw += sock.recv(4096)
    response = raw.decode()

    validate_handshake_response(response, key)

    led = Pin("LED", Pin.OUT)
    period = 100

    timer = Timer()
    timer.init(period=period, callback=lambda v: led.toggle())

    print("websocket connected")

    uname = os.uname()
    device = str(uname.machine) + " " + str(uname.version) + " " + IP
    sock.send((encode_text_message("/device " + device)))

    try:
        while True:
            msg = str(time.ticks_ms())
            False and print(f"-> [{msg}]")
            sock.send(encode_text_message(msg))

            data = sock.recv(4096)
            if not data:
                print("connection closed by server")
                break

            message = decode_text_message(data)
            False and print(f"<- [{message}]")

            echo, period_update = message.split(" ")
            if int(period_update) != period:
                timer.deinit()

                if period == 0:
                    led.off()
                    break

                period = int(period_update)
                timer = Timer()
                timer.init(period=period, callback=lambda v: led.toggle())
                print("led period changed to", period)

    except KeyboardInterrupt:
        print("\nexiting")
    except Exception as e:
        print("error:", e)
    finally:
        sock.close()


print(os.uname())

WIFI_SSID = settings.WIFI_SSID
WIFI_PASSWORD = settings.WIFI_PASSWORD

IPIFY = "https://api.ipify.org"

wlan = network.WLAN(network.STA_IF)


def connect_wifi():
    if wlan.isconnected():
        print("WIFI already connected")
        print("local IP", wlan.ifconfig()[0])
        return True

    print(f"connecting to WIFI network: {WIFI_SSID}...")
    print(wlan.ifconfig())

    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait_s = 20
    start_time = time.ticks_ms()

    led = Pin("LED", Pin.OUT)

    timer = Timer()

    timer.init(period=100, callback=lambda v: led.toggle())

    def timeout():
        return time.ticks_diff(time.ticks_ms(), start_time) < max_wait_s * 1000

    spinner = "\\|/-"
    try:
        while not wlan.isconnected() and timeout():
            status = wlan.status()
            if status == network.STAT_CONNECTING:
                ch, *spinner = spinner
                spinner.append(ch)
                print(f"\r{ch}", end="")
            elif status == network.STAT_WRONG_PASSWORD:
                print("\nerror: wrong WIFI password")
                return False
            elif status == network.STAT_NO_AP_FOUND:
                print("\nerror: SSID not found")
                return False
            elif status == network.STAT_CONNECT_FAIL:
                print("\nerror: connection failed (reason unknown)")
                return False
            # status codes:
            # 0=idle, 1=connecting, 2=wrong pwd, 3=connected, <0=error
            elif status < 0 or status >= 3:
                break
            machine.idle()
    finally:
        timer.deinit()
        led.off()

    print("\r")
    if wlan.isconnected():
        print("WIFI connected")
        print("local IP", wlan.ifconfig()[0])
        return True
    else:
        status = wlan.status()
        print(f"failed to connect to WIFI: {status=}")
        wlan.active(False)
        return False


IP: str | None = None

HOST, PORT, PATH = settings.WS_HOST, settings.WS_PORT, settings.WS_PATH
if connect_wifi():
    response = urequests.get(IPIFY)
    IP = response.text
    print("public IP", IP)

    websocket_client_ssl(HOST, PORT, PATH)
