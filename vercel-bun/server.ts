const page = Bun.file(new URL("./index.html", import.meta.url));

Bun.serve({
  routes: {
    "/": () => new Response(page, {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    }),
    "/health": () => new Response("ok", {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    }),
  },
  fetch(request, server) {
    if (new URL(request.url).pathname === "/ws") {
      if (server.upgrade(request)) return;
      return new Response("WebSocket upgrade required", { status: 426 });
    }
    return new Response("Not found", { status: 404 });
  },
  websocket: {
    message(socket, message) {
      const text = typeof message === "string" ? message : message.toString();
      socket.send(text === "ping" ? "pong" : Array.from(text).reverse().join(""));
    },
  },
});
