import { Buffer } from "node:buffer";

export async function GET({ request }) {
    console.log(request);

    const key = request.headers.get("sec-websocket-key");
    if (!key) throw new Response("Missing sec-websocket-key header", { status: 400 });

    const accept = await createAcceptKey(key);
    const headers = {
        Upgrade: "websocket",
        Connection: "Upgrade",
        "Sec-WebSocket-Accept": accept,
    };

    console.log(`[websocket] stream requested`);

    const stream = new ReadableStream({
        async start(controller) {
            console.log(`[websocket] stream started`);
            for await (const msg of streamer()) {
                controller.enqueue(new TextEncoder().encode(msg));
            }
        },
        async cancel() {
            console.log(`[websocket] stream cancelled`);
        },
    });
    return new Response(stream, { status: 101, headers: headers });
}

function decodeFrame(data: Buffer): string | null {
    const isFinal = (data[0] & 0b10000000) !== 0;
    const opcode = data[0] & 0x0f;
    if (!isFinal || opcode !== 0x1) return null; // only unfragmented text

    const masked = (data[1] & 0b10000000) !== 0;
    let length = data[1] & 0x7f;
    let offset = 2;

    if (length === 126) {
        length = data.readUInt16BE(offset);
        offset += 2;
    } else if (length === 127) {
        length = Number(data.readBigUInt64BE(offset));
        offset += 8;
    }

    let mask: Buffer | undefined;
    if (masked) {
        mask = data.subarray(offset, offset + 4);
        offset += 4;
    }

    const payload = data.subarray(offset, offset + length);
    if (masked && mask) {
        for (let i = 0; i < payload.length; i++) {
            payload[i] ^= mask[i % 4];
        }
    }

    return payload.toString("utf8");
}

function encodeFrame(str: string): Buffer {
    const payload = Buffer.from(str);
    const len = payload.length;

    let header: Buffer;

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

async function createAcceptKey(key: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11");
    const hash = await crypto.subtle.digest("SHA-1", data);
    return Buffer.from(hash).toString("base64");
}

async function* streamer(): AsyncGenerator<Buffer<ArrayBufferLike>, void, unknown> {
    let i = 0;
    const pause = 500;
    while (true) {
        i += 1;
        await new Promise((r) => setTimeout(r, pause));
        const v = { n: i, when: new Date().toISOString(), mode: "ws" };
        yield encodeFrame(JSON.stringify(v));
    }
}
