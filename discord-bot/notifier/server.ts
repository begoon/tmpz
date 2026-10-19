Bun.serve({
  port: Number(process.env.PORT || 3000),
  fetch(request) {
    const path = new URL(request.url).pathname;
    if (path !== "/" && path !== "/health") {
      return new Response("Not found", { status: 404 });
    }
    return Response.json({
      service: "discord-bot",
      status: "ok",
      runtime: `Bun ${Bun.version}`,
      note: "HTTP service is healthy. Discord connection is managed by the discord daemon.",
    });
  },
});
