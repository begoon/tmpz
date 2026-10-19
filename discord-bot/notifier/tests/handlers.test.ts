import { expect, test } from "bun:test";
import { containsAloha, handleCommand, handleForm, handleMessage } from "../src/handlers";
import { MessageFlags, type InteractionReplyOptions, type ModalBuilder } from "discord.js";

test("/mood posts a single-choice 24-hour poll only in the configured guild", async () => {
  const replies: InteractionReplyOptions[] = [];
  const command = { guildId: "guild", commandName: "mood", showModal: async () => {}, reply: async (value: InteractionReplyOptions) => { replies.push(value); } };
  await handleCommand(command, "guild");
  await handleCommand(command, "other");
  expect(replies).toEqual([{
    poll: {
      question: { text: "How are you feeling?" },
      answers: [{ text: "good" }, { text: "ok" }, { text: "bad" }],
      duration: 24,
      allowMultiselect: false,
    },
    allowedMentions: { parse: [] },
  }]);
});

test("/life uploads the vendored PNG only in the configured guild", async () => {
  const replies: InteractionReplyOptions[] = [];
  const command = { guildId: "guild", commandName: "life", showModal: async () => {}, reply: async (value: InteractionReplyOptions) => { replies.push(value); } };
  await handleCommand(command, "guild");
  await handleCommand(command, "other");
  expect(replies).toHaveLength(1);
  const file = replies[0].files![0] as { attachment: string; name: string };
  expect(file.name).toBe("glider.png");
  const bytes = new Uint8Array(await Bun.file(file.attachment).arrayBuffer());
  expect([...bytes.slice(0, 8)]).toEqual([137, 80, 78, 71, 13, 10, 26, 10]);
});

test("matches whole words with punctuation and mixed case", () => {
  for (const text of ["aloha", "ALOHA!", "hello, aloha everyone", "🌺aloha🌺"]) expect(containsAloha(text)).toBe(true);
  for (const text of ["", "alohas", "myaloha", "aloha_world", "éaloha"]) expect(containsAloha(text)).toBe(false);
});

test("replies to users in the configured guild, ignoring bots, webhooks and other guilds", async () => {
  const replies: unknown[] = [];
  const message = { guildId: "guild", author: { bot: false }, webhookId: null, content: "aloha!", reply: async (value: unknown) => { replies.push(value); } };
  await handleMessage(message, "guild");
  await handleMessage({ ...message, author: { bot: true } }, "guild");
  await handleMessage({ ...message, webhookId: "webhook" }, "guild");
  await handleMessage({ ...message, guildId: null }, "guild");
  await handleMessage(message, "other");
  await handleMessage({ ...message, content: "hello" }, "guild");
  expect(replies).toEqual([{ content: "welcome!", allowedMentions: { parse: [], repliedUser: false } }]);
});

test("/ping replies pong! only in the configured guild", async () => {
  const replies: unknown[] = [];
  const command = { guildId: "guild", commandName: "ping", showModal: async () => {}, reply: async (value: unknown) => { replies.push(value); } };
  await handleCommand(command, "guild");
  await handleCommand(command, "other");
  await handleCommand({ ...command, commandName: "unknown" }, "guild");
  expect(replies).toEqual([{ content: "pong!", allowedMentions: { parse: [] } }]);
});

test("/links sends two URL buttons only in the configured guild", async () => {
  const replies: InteractionReplyOptions[] = [];
  const command = { guildId: "guild", commandName: "links", showModal: async () => {}, reply: async (value: InteractionReplyOptions) => { replies.push(value); } };
  await handleCommand(command, "guild");
  await handleCommand(command, "other");
  expect(replies).toHaveLength(1);
  const payload = JSON.parse(JSON.stringify(replies[0]));
  expect(payload.components).toEqual([{ type: 1, components: [
    { type: 2, label: "demin.ws", style: 5, url: "https://demin.ws" },
    { type: 2, label: "demin.page", style: 5, url: "https://demin.page" },
  ] }]);
});

test("/greet opens a modal with two required short inputs", async () => {
  const modals: ModalBuilder[] = [];
  const command = { guildId: "guild", commandName: "greet", showModal: async (modal: ModalBuilder) => { modals.push(modal); }, reply: async () => { throw new Error("Expected a modal"); } };
  await handleCommand(command, "guild");
  await handleCommand(command, "other");
  expect(modals).toHaveLength(1);
  const modal = JSON.parse(JSON.stringify(modals[0]));
  expect(modal.custom_id).toBe("welcome-form");
  expect(modal.components.map((label: any) => ({ label: label.label, id: label.component.custom_id, required: label.component.required, style: label.component.style }))).toEqual([
    { label: "Firstname", id: "firstname", required: true, style: 1 },
    { label: "Surname", id: "surname", required: true, style: 1 },
  ]);
});

test("form submission welcomes the entered name and ignores unrelated submissions", async () => {
  const replies: InteractionReplyOptions[] = [];
  const form = { guildId: "guild", customId: "welcome-form", fields: { getTextInputValue: (id: string) => id === "firstname" ? " Ada " : " Lovelace " }, reply: async (value: InteractionReplyOptions) => { replies.push(value); } };
  await handleForm(form, "guild");
  await handleForm(form, "other");
  await handleForm({ ...form, customId: "other-form" }, "guild");
  expect(replies).toEqual([{ content: "Welcome, Ada Lovelace!", allowedMentions: { parse: [] } }]);
  await handleForm({ ...form, fields: { getTextInputValue: () => "  " } }, "guild");
  expect(replies[1]).toEqual({ content: "Please enter both Firstname and Surname.", flags: MessageFlags.Ephemeral });
});
