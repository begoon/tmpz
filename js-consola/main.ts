import process from "node:process";

import { consola } from "npm:consola";

const kinds = [
    "silent",
    "fatal",
    "error",
    "warn",
    "log",
    "info",
    "success",
    "fail",
    "ready",
    "start",
    "box",
    "debug",
    "verbose",
    // "trace",
] as const;

Date.prototype.toLocaleTimeString = Date.prototype.toISOString;
consola.options.formatOptions.compact = false;
consola.log("default level", consola.level); // 3
if (process.argv.includes("--verbose")) consola.level = 9;
kinds.forEach((kind) => {
    consola[kind]("hello world", kind);
});

consola.box("exception", "box", {
    number: 1,
    boolean: true,
    object: { a: 1 },
    array: [1, 2, 3],
    date: new Date(),
    // error: new Error("hello world"),
    symbol: Symbol("symbol"),
    null: null,
    undefined: undefined,
});
