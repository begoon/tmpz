import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./module.wasm", import.meta.url));
console.log("loading wasm from:", url);
const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), {
    env: {
        print(ptr, len) {
            const bytes = new Uint8Array(instance.exports.memory.buffer, ptr, len);
            const string = new TextDecoder("utf-8").decode(bytes);
            console.log("WASM print:", string);
        },
    },
});

const { func } = instance.exports;

const result = func(1, 0x1122334455667788n, 0x99aabbccddeeff00n) & 0xffffffffffffffffn;
console.log("func():", result.toString(16).padStart(16, "0"));
