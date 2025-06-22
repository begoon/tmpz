const isDeno = typeof Deno !== "undefined";
const isBun = typeof Bun !== "undefined";

if (isDeno) {
    const { serveDir } = await import("jsr:@std/http/file-server");
    Deno.serve((req: Request) => serveDir(req, { fsRoot: "." }));
}

if (isBun) {
    Bun.serve({
        fetch(req: Request) {
            const url = new URL(req.url);
            const path = url.pathname === "/" ? "/index.html" : url.pathname;
            return new Response(Bun.file(`.${path}`));
        },
        port: 8000,
    });
}
