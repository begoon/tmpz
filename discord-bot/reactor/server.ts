import { createHandler } from "./src/interactions";

Bun.serve({
  port: Number(process.env.PORT || 3001),
  fetch: createHandler({
    publicKey: process.env.DISCORD_PUBLIC_KEY,
    applicationId: process.env.DISCORD_APPLICATION_ID,
    guildId: process.env.DISCORD_GUILD_ID,
  }),
});
