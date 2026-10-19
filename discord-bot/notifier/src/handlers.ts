import { ActionRowBuilder, ButtonBuilder, ButtonStyle, LabelBuilder, MessageFlags, ModalBuilder, TextInputBuilder, TextInputStyle, type InteractionReplyOptions } from "discord.js";
import { fileURLToPath } from "node:url";

const gliderPath = fileURLToPath(new URL("../assets/glider.png", import.meta.url));

export function containsAloha(content: string): boolean {
  return /(?:^|[^\p{L}\p{N}_])aloha(?:$|[^\p{L}\p{N}_])/iu.test(content);
}

export interface IncomingMessage {
  guildId: string | null;
  author: { bot: boolean };
  webhookId: string | null;
  content: string;
  reply(options: { content: string; allowedMentions: { parse: []; repliedUser: boolean } }): Promise<unknown>;
}

export async function handleMessage(message: IncomingMessage, guildId: string) {
  if (message.guildId !== guildId || message.author.bot || message.webhookId || !containsAloha(message.content)) return;
  await message.reply({
    content: "welcome!",
    allowedMentions: { parse: [], repliedUser: false },
  });
}

export interface IncomingCommand {
  guildId: string | null;
  commandName: string;
  reply(options: InteractionReplyOptions): Promise<unknown>;
  showModal(modal: ModalBuilder): Promise<unknown>;
}

export async function handleCommand(interaction: IncomingCommand, guildId: string) {
  if (interaction.guildId !== guildId) return;
  if (interaction.commandName === "me") {
    await interaction.reply({ content: "I am Notifier", allowedMentions: { parse: [] } });
  } else if (interaction.commandName === "ping") {
    await interaction.reply({ content: "pong!", allowedMentions: { parse: [] } });
  } else if (interaction.commandName === "mood") {
    await interaction.reply({
      poll: {
        question: { text: "How are you feeling?" },
        answers: [{ text: "good" }, { text: "ok" }, { text: "bad" }],
        duration: 24,
        allowMultiselect: false,
      },
      allowedMentions: { parse: [] },
    });
  } else if (interaction.commandName === "life") {
    await interaction.reply({
      files: [{ attachment: gliderPath, name: "glider.png", description: "A glider pattern from Conway's Game of Life" }],
      allowedMentions: { parse: [] },
    });
  } else if (interaction.commandName === "links") {
    const links = new ActionRowBuilder<ButtonBuilder>().addComponents(
      new ButtonBuilder().setLabel("demin.ws").setStyle(ButtonStyle.Link).setURL("https://demin.ws"),
      new ButtonBuilder().setLabel("demin.page").setStyle(ButtonStyle.Link).setURL("https://demin.page"),
    );
    await interaction.reply({ components: [links], allowedMentions: { parse: [] } });
  } else if (interaction.commandName === "greet") {
    const modal = new ModalBuilder().setCustomId("welcome-form").setTitle("Your name").addLabelComponents(
      new LabelBuilder().setLabel("Firstname").setTextInputComponent(
        new TextInputBuilder().setCustomId("firstname").setStyle(TextInputStyle.Short).setRequired(true).setMaxLength(100),
      ),
      new LabelBuilder().setLabel("Surname").setTextInputComponent(
        new TextInputBuilder().setCustomId("surname").setStyle(TextInputStyle.Short).setRequired(true).setMaxLength(100),
      ),
    );
    await interaction.showModal(modal);
  }
}

export interface IncomingForm {
  guildId: string | null;
  customId: string;
  fields: { getTextInputValue(id: string): string };
  reply(options: InteractionReplyOptions): Promise<unknown>;
}

export async function handleForm(interaction: IncomingForm, guildId: string) {
  if (interaction.guildId !== guildId || interaction.customId !== "welcome-form") return;
  const firstname = interaction.fields.getTextInputValue("firstname").trim();
  const surname = interaction.fields.getTextInputValue("surname").trim();
  if (!firstname || !surname) {
    await interaction.reply({ content: "Please enter both Firstname and Surname.", flags: MessageFlags.Ephemeral });
    return;
  }
  await interaction.reply({ content: `Welcome, ${firstname} ${surname}!`, allowedMentions: { parse: [] } });
}
