import { cron } from "@elysiajs/cron";
import { html } from "@elysiajs/html";
import { staticPlugin } from "@elysiajs/static";
import { swagger } from "@elysiajs/swagger";
import { Elysia, t } from "elysia";

const page = `<!DOCTYPE HTML>
<html lang="en">
    <head>
        <title>HTML</title>
    </head>
    <body>
        <h1>ElysiaJS HTML</h1>
    </body>
</html>`;

const app = new Elysia()
    .use(staticPlugin({ prefix: "/static", assets: "public" }))
    .use(
        cron({
            name: "heartbeat",
            pattern: "*/10 * * * * *",
            run() {
                console.log("Heartbeat");
            },
        })
    )
    .use(html())
    .use(
        swagger({
            path: "/swagger",
            documentation: { info: { title: "Elysia API", version: "1.0.0" } },
        })
    )
    .get("/image", () => Bun.file("public/logo.png"))
    .get("/html", ({ html }) => html(page))
    .get("/ping", () => "pong")
    .get("/echo/:id/*", ({ params, query }) => ({ params, query }))
    .post("/echo/:id/*", ({ params, body }) => {
        return {
            params,
            body,
        };
    })
    .post("/choice", ({ body }) => ({ body }), { type: "json" })
    .post("/choice", ({ body }) => "text?\n" + body, {
        type: "text",
    })
    .post("/mirror", ({ body }) => body, {
        body: t.Object({
            username: t.String(),
            password: t.String(),
        }),
    })
    .get("/", () => "Elysia API")
    .onParse(({ request }, contentType) => {
        if (contentType === "application/json") return request.json();
        if (contentType === "text/plain") return request.text();
    })
    .listen(3000);

console.log(
    `🦊 Elysia is running at ${app.server?.hostname}:${app.server?.port}`
);
