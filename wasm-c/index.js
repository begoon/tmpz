import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./module.wasm", import.meta.url));
console.log("Loading wasm from:", url);
const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), {});

const { memory, native_function, native_string, alloc, __heap_base, __data_end } = instance.exports;

console.log("WASM memory size (pages):", memory.buffer.byteLength / 65536);
console.log("WASM exports:", Object.keys(instance.exports));

// typed views over the shared linear memory
const u8 = new Uint8Array(memory.buffer);
const i32 = new Int32Array(memory.buffer);

// helper: write a C string (UTF-8, null-terminated) into wasm memory
function write_cstring(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const ptr = alloc(data.length + 1);
    u8.set(data, ptr);
    u8[ptr + data.length] = 0;
    return ptr;
}

// helper: allocate 4 bytes and store an int32
function write_int32(value) {
    const ptr = alloc(4);
    i32[ptr >> 2] = value;
    return ptr;
}

function read_cstring(ptr) {
    const decoder = new TextDecoder();
    let end = ptr;
    while (u8[end] !== 0) end++;
    return decoder.decode(u8.subarray(ptr, end));
}

const x = 7;
const y_ptr = write_int32(5); // initial *y = 5
const s_ptr = write_cstring("abc"); // len = 3

const sz = native_function(x, y_ptr, s_ptr);

console.log("returned length:", sz);
console.log("updated *y:", i32[y_ptr >> 2]);

const X = BigInt(0xabcdfa000000000000bfn);
console.log("wasm string: ", read_cstring(native_string(X)));

if (__heap_base && __data_end) {
    console.log("__data_end:", __data_end.value, "__heap_base:", __heap_base.value);
}
