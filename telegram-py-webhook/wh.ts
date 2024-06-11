import chalk from "npm:chalk@5.3.0";
import { Telegram } from "./telegram.ts";

const {
    bold: { red },
} = chalk;

export async function installWebhook(base: string) {
    const BOT_TOKEN = Deno.env.get("BOT_TOKEN");
    if (!BOT_TOKEN) throw new Error("BOT_TOKEN is not set");

    console.log({ bot: BOT_TOKEN });
    const telegram = new Telegram(BOT_TOKEN);

    const prefix = base.includes("django") ? "update" : "bot";
    const wh = base + "/" + prefix;
    console.info({ webhook: wh });
    if (!(await telegram.setWebhook(wh))) throw new Error("setWebhook failed");

    try {
        const health = base + "/health";
        console.log({ health });
        const response = await (await fetch(health)).json();
        console.log({ health: response });
    } catch (_e) {
        console.error(red("health check failed"));
    }
}

export async function deleteWebhook() {
    const BOT_TOKEN = Deno.env.get("BOT_TOKEN");
    if (!BOT_TOKEN) throw new Error("BOT_TOKEN is not set");

    console.log({ bot: BOT_TOKEN });
    const telegram = new Telegram(BOT_TOKEN);
    if (!(await telegram.deleteWebhook()))
        throw new Error("deleteWebhook failed");

    console.info("webhook deleted");
}

export async function webhookInfo() {
    const BOT_TOKEN = Deno.env.get("BOT_TOKEN");
    if (!BOT_TOKEN) throw new Error("BOT_TOKEN is not set");

    console.log({ bot: BOT_TOKEN });
    const telegram = new Telegram(BOT_TOKEN);
    console.log(await telegram.getWebhookInfo());
}
