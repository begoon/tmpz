import { embeddedFiles, file } from "bun";
// @ts-ignore
import icon from "./public/3948225.avif" with { type: "file" };
import data from "./public/data.json" with { type: "json" };

import { staticPlugin } from "@elysiajs/static";
import { swagger } from "@elysiajs/swagger";
import { Elysia } from "elysia";

const api = new Elysia()
    .use(staticPlugin({prefix: "/fs", indexHTML: true}))
    .use(swagger())
    .get("/", () => "ha?")
    .get("/api", () => "/api/*")
    .post("/post", () => "postage")

Bun.serve({
    fetch(req) {
        const { pathname } = new URL(req.url);
        if (pathname === "/icon") return new Response(file(icon));
        if (pathname === "/data") return new Response(JSON.stringify(data));
        if (pathname === "/ls") return new Response(JSON.stringify(embeddedFiles.map(f => f.name)));
        return api.handle(req);
    },
});
    