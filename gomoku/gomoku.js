import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./gomoku.wasm", import.meta.url));
console.log("loading wasm from:", url);
const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), {
    env: {
        console: (ptr, len) => {
            const memory = instance.exports.memory;
            const bytes = new Uint8Array(memory.buffer, ptr, len);
            const text = new TextDecoder("utf-8").decode(bytes);
            process.stdout.write(text);
        },
        enter: () => {
            prompt("press enter to continue...");
        },
        status: (ptr, len) => {},
    },
});

const { loopback } = instance.exports;

loopback();
