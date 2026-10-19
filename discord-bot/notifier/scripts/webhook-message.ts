const content = process.argv[2] ?? "ok";
if (!content.trim() || content.length > 2000) {
  console.error("Message must contain 1–2000 characters and cannot be blank.");
  process.exit(1);
}

const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
if (!webhookUrl) {
  console.error("Set DISCORD_WEBHOOK_URL in .env.");
  process.exit(1);
}

try {
  const url = new URL(webhookUrl);
  if (url.protocol !== "https:" || url.hostname !== "discord.com" || !/^\/api\/(?:v\d+\/)?webhooks\/\d+\/[^/]+$/.test(url.pathname)) {
    console.error("DISCORD_WEBHOOK_URL must be a Discord HTTPS webhook URL.");
    process.exit(1);
  }
  // Wait for Discord to confirm the message was created.
  url.searchParams.set("wait", "true");
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, allowed_mentions: { parse: [] } }),
    signal: AbortSignal.timeout(15_000),
    redirect: "error",
  });
  if (!response.ok) {
    console.error(`Discord returned HTTP ${response.status}. Check the webhook URL and retry later if rate limited.`);
    process.exit(1);
  }
  const message = await response.json() as { id: string; channel_id: string };
  console.log(`Webhook message sent: ${message.id} (channel ${message.channel_id})`);
} catch {
  // Do not print the error: it may contain the secret webhook URL.
  console.error("Could not confirm the webhook message. Check the URL and network connection; check the channel before retrying.");
  process.exit(1);
}

export {};
