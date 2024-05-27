import chalk from "npm:chalk@5.3.0";
import { Telegram } from "./telegram.ts";

const {
    bold: { red },
} = chalk;

export async function installWebhook(url: string) {
    const BOT_TOKEN = Deno.env.get("BOT_TOKEN");
    if (!BOT_TOKEN) throw new Error("BOT_TOKEN is not set");

    console.log({ bot: BOT_TOKEN });
    const telegram = new Telegram(BOT_TOKEN);

    console.info({ webhook: url });
    if (!(await telegram.setWebhook(url))) throw new Error("setWebhook failed");

    try {
        const base = url.split("/bot")[0];
        const health = await (await fetch(base + "/health")).json();
        console.log(health);
    } catch (_e) {
        console.error(red("health check failed"));
    }
}
