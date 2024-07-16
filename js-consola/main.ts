import process from "node:process";
const argv = process.argv;

import { LogType, consola } from "consola";
import { colors } from "consola/utils";

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
consola.options.formatOptions.compact = !false;
consola.options.formatOptions.columns = 1;

consola.log("default level", consola.level); // 3

if (argv.includes("--verbose"))
    consola.level = consola.options.types.verbose.level!;

const i = argv.indexOf("--loglevel");
if (i && argv[i + 1]) {
    const level = argv[i + 1] as LogType;
    process.env.CONSOLA_LEVEL = level;
}

const error = argv.includes("--error");

// console.log("types", consola.options.types);

kinds.forEach((kind) => {
    consola[kind]("hello world", colors.redBright(kind));
});

consola.box("exception", "box", {
    number: 1,
    boolean: true,
    object: { a: 1 },
    array: [1, 2, 3],
    date: new Date(),
    error: new Error("hello world"),
    symbol: Symbol("symbol"),
    null: null,
    undefined: undefined,
});
