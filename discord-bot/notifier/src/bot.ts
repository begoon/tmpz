import { Client, Events, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from "discord.js";
import { handleCommand, handleForm, handleMessage } from "./handlers";

const token = process.env.DISCORD_BOT_TOKEN;
const applicationId = process.env.DISCORD_APPLICATION_ID;
const guildId = process.env.DISCORD_GUILD_ID;
if (!token || !applicationId || !guildId) {
  throw new Error("Set DISCORD_BOT_TOKEN, DISCORD_APPLICATION_ID and DISCORD_GUILD_ID.");
}

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

client.once(Events.ClientReady, async (ready) => {
  console.log(`Connected as ${ready.user.tag}`);
  try {
    // POST upserts our commands and preserves other application commands.
    const rest = new REST({ version: "10" }).setToken(token);
    for (const command of [
      new SlashCommandBuilder().setName("ping").setDescription("Reply with pong!"),
      new SlashCommandBuilder().setName("me").setDescription("Open demin.ws and demin.page"),
      new SlashCommandBuilder().setName("greet").setDescription("Enter your first name and surname"),
      new SlashCommandBuilder().setName("life").setDescription("Show a Game of Life glider"),
    ]) {
      await rest.post(Routes.applicationGuildCommands(applicationId, guildId), { body: command.toJSON() });
    }
    console.log("Registered /ping, /me, /greet and /life in the configured server.");
  } catch {
    console.error("Command registration failed. Check application ID, server ID and bot installation.");
    await client.destroy();
    process.exit(1);
  }
});

client.on(Events.MessageCreate, (message) => {
  void handleMessage(message, guildId).catch(() => console.error("Could not reply to a message. Check channel permissions."));
});
client.on(Events.InteractionCreate, (interaction) => {
  if (interaction.isChatInputCommand()) {
    void handleCommand(interaction, guildId).catch(() => console.error("Could not reply to a slash command."));
  } else if (interaction.isModalSubmit()) {
    void handleForm(interaction, guildId).catch(() => console.error("Could not reply to a form submission."));
  }
});
client.on(Events.Error, () => console.error("Discord client error."));

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, async () => {
    await client.destroy();
    process.exit(0);
  });
}

try {
  await client.login(token);
} catch {
  console.error("Discord login failed. Check bot token and enable Message Content Intent in the Developer Portal.");
  await client.destroy();
  process.exit(1);
}
