import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./module.wasm", import.meta.url));
console.log("loading wasm from:", url);

const env = {
    __panic_abort: (ptr, len) => {
        throw new Error("panic", { ptr, len });
    },
};

const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), { env });

const { memory, alloc, dealloc, process } = instance.exports;

console.log("WASM exports:", Object.keys(instance.exports));

const u8 = new Uint8Array(memory.buffer);

function read_cstring(ptr, len) {
    const decoder = new TextDecoder();
    console.log("reading cstring at", "0x" + ptr.toString(16), "len", len);
    for (let i = 0; i < len; i++) {
        console.log("byte", i, u8[ptr + i]);
    }
    return decoder.decode(u8.subarray(ptr, ptr + len));
}

function write_cstring(ptr, str) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(str + "\0");
    u8.set(bytes, ptr);
    return ptr;
}

const v = alloc(16);
console.log("allocated 16 bytes at", "0x" + v.toString(16));

write_cstring(v, "WASM, V!");

const r = process(v, 7);
console.log("read back:", r);
console.log("read back string:", read_cstring(...r));

dealloc(v);
console.log("deallocated at", "0x" + v.toString(16));
