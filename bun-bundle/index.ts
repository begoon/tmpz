const embeddedLookup: Record<string, Blob> = {};
for (const blob of Bun.embeddedFiles as (Blob & { name: string })[]) {
    const name = blob.name.replace(/^static\//, "").replace(/-[a-f0-9]+\./, ".");
    embeddedLookup[`/${name}`] = blob;
}

const server = Bun.serve({
    port: Number(process.env.PORT) || 3000,
    routes: {
        "/version": {
            GET: () => Response.json({ status: "live" }),
        },
    },
    async fetch(req) {
        const url = new URL(req.url);
        const path = url.pathname === "/" ? "/index.html" : url.pathname;

        const embedded = embeddedLookup[path];
        if (embedded) return new Response(embedded);

        const file = Bun.file(`./static${path}`);
        if (await file.exists()) return new Response(file);

        return new Response("Not Found", { status: 404 });
    },
});

console.log(`server running at http://localhost:${server.port}`);
