function ws(sock: WebSocket) {
    sock.onopen = () => {
        console.log("websocket open");
        sock.send(`connected to ${Deno.hostname()}`);
    };
    sock.onmessage = (event) => {
        if (typeof event.data === "string") {
            sock.send(event.data);
        }
    };
    sock.onerror = (error) => console.error("websocket error:", error);
    sock.onclose = (e) => console.log("websocket closed", e.code, e.reason);
}

Deno.serve({ port: 8000 }, async (req) => {
    const { pathname } = new URL(req.url);

    if (pathname === "/") {
        const html = await Deno.readTextFile("index.html");
        return new Response(html, { headers: { "Content-Type": "text/html" } });
    }

    if (pathname === "/ws") {
        const { response, socket } = Deno.upgradeWebSocket(req);
        ws(socket);
        return response;
    }

    return new Response("ha?", { status: 404 });
});
