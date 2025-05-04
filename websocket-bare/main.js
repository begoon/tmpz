import crypto from "node:crypto";
import http from "node:http";

const WS_UUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

function createAcceptKey(secWebSocketKey) {
    return crypto
        .createHash("sha1")
        .update(secWebSocketKey + WS_UUID, "utf8")
        .digest("base64");
}

function decodeFrame(buffer) {
    const isFinal = (buffer[0] & 0b10000000) !== 0;
    const opcode = buffer[0] & 0x0f;

    // Only handle final text frames.
    if (!isFinal || opcode !== 0x1) return null;

    const isMasked = (buffer[1] & 0b10000000) !== 0;
    let length = buffer[1] & 0x7f;
    let offset = 2;

    if (length === 126) {
        length = buffer.readUInt16BE(offset);
        offset += 2;
    } else if (length === 127) {
        length = Number(buffer.readBigUInt64BE(offset));
        offset += 8;
    }

    let mask;
    if (isMasked) {
        mask = buffer.slice(offset, offset + 4);
        offset += 4;
    }

    const payload = buffer.slice(offset, offset + length);
    if (isMasked) {
        for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i % 4];
    }
    return payload.toString("utf8");
}

function encodeFrame(str) {
    const payload = Buffer.from(str);
    const len = payload.length;

    let header;
    if (len < 126) {
        header = Buffer.from([0x81, len]);
    } else if (len < 65536) {
        header = Buffer.alloc(4);
        header[0] = 0x81;
        header[1] = 126;
        header.writeUInt16BE(len, 2);
    } else {
        header = Buffer.alloc(10);
        header[0] = 0x81;
        header[1] = 127;
        header.writeBigUInt64BE(BigInt(len), 2);
    }

    return Buffer.concat([header, payload]);
}

const server = http.createServer((req, res) => {
    res.writeHead(426, { "Content-Type": "text/plain" });
    res.end("This server only supports WebSocket connections.\n");
});

server.on("upgrade", (req, socket) => {
    console.log("upgrade()", req.headers);
    const key = req.headers["sec-websocket-key"];
    if (!key) {
        socket.destroy();
        return;
    }

    const acceptKey = createAcceptKey(key);
    const headers = [
        "HTTP/1.1 101 Switching Protocols",
        "Upgrade: websocket",
        "Connection: Upgrade",
        `Sec-WebSocket-Accept: ${acceptKey}`,
        "\r\n",
    ];

    socket.write(headers.join("\r\n"));
    console.log("headers:", headers.join("\r\n"));

    socket.on("data", (chunk) => {
        console.log("data()", chunk);
        const message = decodeFrame(chunk);
        if (message) {
            console.log("received:", message);
            const response = encodeFrame(message);
            socket.write(response);
        }
    });

    socket.on("end", () => {
        console.log("client disconnected");
    });
});

server.listen(3000, () => {
    console.log("websocket server listening on ws://localhost:3000");
});
