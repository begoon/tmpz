const server = Bun.serve({
    port: 3000,
    routes: {
        "/": new Response(await Bun.file("index.html").text(), {
            headers: { "Content-Type": "text/html" },
        }),
        "/beacon": async (req) => {
            const data = await req.text();
            console.log("beacon data:", data);
            return Response.json({ message: "beacon received", data });
        },
    },
});

console.log(`listening on http://localhost:${server.port}`);

export {};
