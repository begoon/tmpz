import { ChannelType, REST, Routes } from "discord.js";

const content = process.argv[2] ?? "ok";
if (!content.trim() || content.length > 2000) {
  console.error("Message must contain 1–2000 characters and cannot be blank.");
  process.exit(1);
}

const token = process.env.DISCORD_BOT_TOKEN;
const guildId = process.env.DISCORD_GUILD_ID;
if (!token || !guildId) {
  console.error("Set DISCORD_BOT_TOKEN and DISCORD_GUILD_ID in .env.");
  process.exit(1);
}

try {
  const rest = new REST({ version: "10", timeout: 15_000, retries: 0 }).setToken(token);
  const channels = await rest.get(Routes.guildChannels(guildId)) as Array<{ id: string; name: string; type: number }>;
  const matches = channels.filter(channel => channel.name === "general" && channel.type === ChannelType.GuildText);
  if (matches.length !== 1) {
    console.error(`Expected exactly one #general text channel in the configured server; found ${matches.length}.`);
    process.exit(1);
  }
  const channel = matches[0];
  const message = await rest.post(Routes.channelMessages(channel.id), {
    body: { content, allowed_mentions: { parse: [] } },
  }) as { id: string };
  console.log(`Sent to #general: https://discord.com/channels/${guildId}/${channel.id}/${message.id}`);
} catch {
  console.error("Could not send the message. Check connectivity, bot credentials, and View Channel / Send Messages permissions. Check the channel before retrying.");
  process.exit(1);
}
