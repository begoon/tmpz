import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./build/module.wasm", import.meta.url));
console.log("Loading wasm from:", url);
const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), {});

const { memory, native_function, alloc, __heap_base, __data_end } = instance.exports;

console.log("WASM memory size (pages):", memory.buffer.byteLength / 65536);
console.log("WASM exports:", Object.keys(instance.exports));

// typed views over the shared linear memory
const u8 = new Uint8Array(memory.buffer);
const i32 = new Int32Array(memory.buffer);

// helper: write a C string (UTF-8, null-terminated) into wasm memory
function writeCString(str) {
    const enc = new TextEncoder();
    const data = enc.encode(str);
    const ptr = alloc(data.length + 1);
    u8.set(data, ptr);
    u8[ptr + data.length] = 0;
    return ptr;
}

// helper: allocate 4 bytes and store an int32
function writeInt32(value) {
    const ptr = alloc(4);
    i32[ptr >> 2] = value;
    return ptr;
}

const x = 7;
const y_ptr = writeInt32(5); // initial *y = 5
const s_ptr = writeCString("abc"); // len = 3

const retLen = native_function(x, y_ptr, s_ptr);

console.log("returned length:", retLen);
console.log("updated *y:", i32[y_ptr >> 2]);

if (__heap_base && __data_end) {
    console.log("__data_end:", __data_end.value, "__heap_base:", __heap_base.value);
}
