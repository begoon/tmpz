import { createPublicKey, verify } from "node:crypto";

interface Config { publicKey?: string; applicationId?: string; guildId?: string }

export function createHandler(config: Config) {
  const key = config.publicKey && /^[a-f\d]{64}$/i.test(config.publicKey)
    ? createPublicKey({ key: Buffer.from(`302a300506032b6570032100${config.publicKey}`, "hex"), format: "der", type: "spki" })
    : null;

  return async (request: Request): Promise<Response> => {
    const path = new URL(request.url).pathname;
    if ((path === "/" || path === "/health") && request.method === "GET") {
      return Response.json({ service: "reactor", runtime: `Bun ${Bun.version}`, configured: Boolean(key && config.applicationId && config.guildId) });
    }
    if (path !== "/interactions") return new Response("Not found", { status: 404 });
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: { Allow: "POST" } });
    if (!key || !config.applicationId || !config.guildId) return new Response("Discord configuration missing", { status: 503 });

    const signature = request.headers.get("x-signature-ed25519") ?? "";
    const timestamp = request.headers.get("x-signature-timestamp") ?? "";
    if (!/^[a-f\d]{128}$/i.test(signature) || !/^\d+$/.test(timestamp) || Math.abs(Date.now() / 1000 - Number(timestamp)) > 300) {
      return new Response("Invalid signature", { status: 401 });
    }
    const body = Buffer.from(await request.arrayBuffer());
    if (!verify(null, Buffer.concat([Buffer.from(timestamp), body]), key, Buffer.from(signature, "hex"))) {
      return new Response("Invalid signature", { status: 401 });
    }
    let interaction;
    try { interaction = JSON.parse(body.toString("utf8")); }
    catch { return new Response("Invalid JSON", { status: 400 }); }
    if (!interaction || typeof interaction !== "object") return new Response("Invalid interaction", { status: 400 });
    if (interaction.type === 1) return Response.json({ type: 1 });
    if (interaction.application_id !== config.applicationId || interaction.guild_id !== config.guildId) {
      return new Response("Forbidden", { status: 403 });
    }
    if (interaction.type === 2 && interaction.data?.name === "me") {
      return Response.json({ type: 4, data: { content: "I am Reactor", allowed_mentions: { parse: [] } } });
    }
    if (interaction.type === 2 && interaction.data?.name === "info") {
      return Response.json({ type: 4, data: {
        content: `Bun version: ${Bun.version}\nDate/time (UTC): ${new Date().toISOString()}`,
        allowed_mentions: { parse: [] },
      } });
    }
    return Response.json({ type: 4, data: { content: "Unknown command.", flags: 64 } });
  };
}
