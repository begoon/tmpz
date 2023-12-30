import process from "node:process";

const N = 1 * 1024 * 1024;
const bytes = new Uint8Array(N).map((_, i) => i % 256);

console.log(bytes.length);

const host = process.argv[2] || "http://127.0.0.1:3000";
const url = host + "/ws/" + crypto.randomUUID();
console.log("connecting to", url);

const ws = new WebSocket(url);
ws.binaryType = "arraybuffer";

ws.onopen = () => {
    console.log("connected");
    ws.send(bytes);
    console.log("-> sent", bytes.length);
};

ws.onclose = (e) => {
    console.log("disconnected", e.code, e.reason);
};

ws.onmessage = (event) => {
    console.log("response:", event.data);
    const received = event.data;
    console.log("<-", received);
    ws.close(1000, "done");
};
