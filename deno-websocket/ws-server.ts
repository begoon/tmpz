Deno.serve({ port: 10000 }, (req) => {
    if (req.headers.get("upgrade") != "websocket") {
        return new Response(null, { status: 501 });
    }
    const { socket, response } = Deno.upgradeWebSocket(req);
    socket.addEventListener("open", () => {
        console.log("client connected");
    });
    socket.addEventListener("close", (e) => {
        console.log("client disconnected", e.code, e.reason);
    });
    socket.addEventListener("message", (event) => {
        console.log("message", event.data);
        if (event.data === "ping") {
            socket.send("pong");
        } else if (event.data === "bye") {
            socket.close();
        } else {
            socket.send(event.data + "?");
        }
    });
    return response;
});
