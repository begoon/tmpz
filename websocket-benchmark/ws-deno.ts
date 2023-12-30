Deno.serve({ port: 3000 }, (req) => {
    if (req.headers.get("upgrade") != "websocket") {
        return new Response(null, { status: 501 });
    }
    const { socket, response } = Deno.upgradeWebSocket(req);
    socket.addEventListener("open", () => {
        console.log("connected");
    });
    socket.addEventListener("message", (event) => {
        const msg = `received ${event.data.size} bytes`;
        console.log(msg);
        socket.send(msg);
    });
    return response;
});
