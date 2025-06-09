import { serveDir } from "jsr:@std/http/file-server";
Deno.serve(async (req: Request) => {
    const url = new URL(req.url);
    if (url.pathname === "/abc") return await fetch("https://httpbin.org/uuid");
    return serveDir(req, { fsRoot: "." });
});
