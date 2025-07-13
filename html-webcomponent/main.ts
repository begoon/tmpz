Bun.serve({
    fetch(req: Request) {
        const url = new URL(req.url);
        const path = url.pathname === "/" ? "/index.html" : url.pathname;
        if (path === "/.well-known/appspecific/com.chrome.devtools.json") return new Response("OK");
        return new Response(Bun.file(`.${path}`));
    },
    port: 8000,
});
