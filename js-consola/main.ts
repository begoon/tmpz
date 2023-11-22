import process from "node:process";
const argv = process.argv;

import { LogType, consola } from "npm:consola";
import { colors } from "npm:consola/utils";

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
    "trace",
] as const;

Date.prototype.toLocaleTimeString = Date.prototype.toISOString;
consola.options.formatOptions.compact = false;

consola.log("default level", consola.level); // 3

if (argv.includes("--verbose"))
    consola.level = consola.options.types.verbose.level!;

const i = argv.indexOf("--loglevel");
if (i && argv[i + 1])
    consola.level = consola.options.types[argv[i + 1] as LogType]?.level || 0;

console.log("types", consola.options.types);

kinds.forEach((kind) => {
    consola[kind]("hello world", colors.redBright(kind));
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
