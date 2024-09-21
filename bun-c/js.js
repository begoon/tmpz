import { cc, ptr } from "bun:ffi";

export const {
    symbols: { native },
} = cc({
    source: "./native.c",
    symbols: { native: { returns: "int", args: ["ptr"] } },
});

const account = Buffer.from("bun-js RUNS c!\0");

console.log("JS:", native(ptr(account)));
console.log("JS:", Buffer.from(account).toString());
