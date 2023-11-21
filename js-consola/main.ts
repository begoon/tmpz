import { consola } from "npm:consola";

Date.prototype.toLocaleTimeString = Date.prototype.toISOString;

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
    "trace",
    "verbose",
] as const;

kinds.forEach((kind) => {
    consola[kind]("hello world");
});
