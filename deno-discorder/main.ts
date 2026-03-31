import nacl from "https://cdn.skypack.dev/tweetnacl@v1.0.3?dts";

const { env } = Deno;

const BOT_TOKEN = env.get("BOT_TOKEN");
const DISCORD_PUBLIC_KEY = env.get("DISCORD_PUBLIC_KEY");

const ROOT_ROUTE = new URLPattern({ pathname: "/" });

Deno.serve(async (req: Request) => {
  if (ROOT_ROUTE.exec(req.url)) return await home(req);
  return Response.json({ error: "ha?" }, { status: 418 });
});

async function home(request: Request) {
  if (request.method != "POST") return Response.json(
    { error: request.method + "?" },
    { status: 418 }
  );
  const { valid, body } = await verifySignature(request);
  if (!valid) {
    console.error("invalid", { request });
    return Response.json({ error: "invalid request"}, { status: 401 });
  }
  const { type = 0, data = { options: [] } } = JSON.parse(body);
  console.info("REQUEST", type, data);

  // Type 1 / Ping
  if (type === 1) {
    return Response.json({
      type: 1, // Type 1 in a response is a Pong interaction response type.
    });
  }

  // Type 2 / ApplicationCommand
  if (type === 2) {
    if (data.name == "ping") return Response.json({type: 4, data: {content: "PONG"}});
    const { value } = data.options.find((option) => option.name === "name");
    return Response.json({
      type: 4,
      data: { content: `aloha, ${value}!` },
    });
  }

  return Response.json({ error: "bad request" }, { status: 400 });
}

// Gateway connection for receiving events
const socket = new WebSocket("wss://gateway.discord.gg/?v=10&encoding=json");

const intents = (1 << 0) | (1 << 9) | (1 << 10) | (1 << 15);

socket.onopen = async () => {
  console.log("connected to discord gateway");

  await socket.send(JSON.stringify({
    op: 2, // OpCode.Identify
    d: {
      token: BOT_TOKEN,
      intents: intents,
      properties: {
        $os: "linux",
        $browser: "deno",
        $device: "deno",
      },
    },
  }));
};

socket.onmessage = async (event) => {
  const payload = JSON.parse(event.data); // as GatewayPayload

  // Handle events here
  console.log("ws", `op=${payload.op} t=${payload.t || "?"}`);

  if (payload.op === 0) { // OpCode.Dispatch
    if (payload.t === "MESSAGE_CREATE") {
      const message = payload.d;
      console.log("ws message", JSON.stringify(message));
      console.log(`new message in ${message.channel_id}: [${message.content}]`);
      // ...
    }
  }
  // Handle other gateway events (e.g., heartbeats) if needed.
};

socket.onerror = (error) => {
  console.error("ws error", error);
};

socket.onclose = (event) => {
  console.log("ws closed");
};

async function verifySignature(
  request: Request,
): Promise<{ valid: boolean; body: string }> {
  const signature = request.headers.get("X-Signature-Ed25519")!;
  const timestamp = request.headers.get("X-Signature-Timestamp")!;
  const body = await request.text();
  const valid = nacl.sign.detached.verify(
    new TextEncoder().encode(timestamp + body),
    hexToUint8Array(signature),
    hexToUint8Array(DISCORD_PUBLIC_KEY),
  );

  return { valid, body };
}

function hexToUint8Array(hex: string) {
  return new Uint8Array(
    hex.match(/.{1,2}/g)!.map((val) => parseInt(val, 16)),
  );
}
