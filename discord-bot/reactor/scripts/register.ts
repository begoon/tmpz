const { DISCORD_APPLICATION_ID: appId, DISCORD_BOT_TOKEN: token, DISCORD_GUILD_ID: guildId } = process.env;
if (!appId || !token || !guildId || appId === "1048889942148907049") {
  throw new Error("Set reactor's separate application ID, bot token and guild ID in reactor/.env.");
}
const headers = { Authorization: `Bot ${token}`, "Content-Type": "application/json" };
const identity = await fetch("https://discord.com/api/v10/applications/@me", { headers });
if (!identity.ok || (await identity.json()).id !== appId) throw new Error("Bot token does not match the reactor application.");
for (const command of [
  { name: "info", description: "Show Bun version and current UTC date/time", type: 1 },
  { name: "me", description: "Identify this bot", type: 1 },
]) {
  const response = await fetch(`https://discord.com/api/v10/applications/${appId}/guilds/${guildId}/commands`, {
    method: "POST", headers,
    body: JSON.stringify(command),
  });
  if (!response.ok) throw new Error(`Registration failed: HTTP ${response.status}. Check installation and server access.`);
}
console.log("Registered /info and /me.");
export {};
