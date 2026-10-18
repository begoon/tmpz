const scope = process.argv[2];
if (scope !== "global" && scope !== "server") {
  console.error("Usage: bun scripts/list-commands.ts <global|server>");
  process.exit(1);
}

const token = process.env.DISCORD_BOT_TOKEN;
const applicationId = process.env.DISCORD_APPLICATION_ID;
const guildId = process.env.DISCORD_GUILD_ID;
if (!token || !applicationId || (scope === "server" && !guildId)) {
  console.error("Set DISCORD_BOT_TOKEN and DISCORD_APPLICATION_ID in .env; server commands also require DISCORD_GUILD_ID.");
  process.exit(1);
}

const path = scope === "global"
  ? `/applications/${applicationId}/commands`
  : `/applications/${applicationId}/guilds/${guildId}/commands`;

try {
  const response = await fetch(`https://discord.com/api/v10${path}`, {
    headers: { Authorization: `Bot ${token}` },
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) {
    console.error(`Discord returned HTTP ${response.status}. Check credentials, application/server IDs, and bot access.`);
    process.exit(1);
  }
  console.log(JSON.stringify(await response.json(), null, 2));
} catch {
  console.error("Could not fetch Discord commands. Check your network connection and try again.");
  process.exit(1);
}

export {};
