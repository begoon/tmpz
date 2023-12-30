// @ts-ignore: ts(2304)
const server = Bun.serve({
    fetch(req: Request, server: WebSocket) {
        // @ts-ignore: ts(2339)
        const success = server.upgrade(req);
        if (success) return undefined;
        return new Response(null, { status: 501 });
    },
    websocket: {
        async message(ws: WebSocket, message: Uint8Array) {
            const msg = `received ${message.length} bytes`;
            console.log(msg);
            await ws.send(msg);
        },
    },
});

console.log(`listening on ${server.hostname}:${server.port}`);
