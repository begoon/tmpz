#!/usr/bin/env -S deno run -A --env

import process, { argv, env } from "node:process";

import { serveDir } from "@std/http/file-server";

import consola from "consola";

import type { Message, ReplyKeyboardMarkup, Update } from "npm:@types/node-telegram-bot-api";

// #region telegram

import type { BotCommand, File, InlineKeyboardMarkup, ParseMode, WebhookInfo } from "npm:@types/node-telegram-bot-api";

let TunnelURL: string | undefined;

export class Telegram {
    static API = "https://api.telegram.org";

    token: string;

    constructor(token: string) {
        this.token = token;
    }

    file(path: string) {
        return `${Telegram.API}/file/bot${this.token}/${path}`;
    }

    async answerCallbackQuery(callback_query_id: string, text?: string) {
        return await this._command("answerCallbackQuery", {
            callback_query_id,
            text,
        });
    }

    async sendMessage(
        chat_id: number,
        text: string,
        options: {
            reply_markup?: InlineKeyboardMarkup | ReplyKeyboardMarkup;
            parse_mode?: ParseMode;
        } & { [key: string]: unknown } = {}
    ) {
        const args = { chat_id, text, ...options };
        return await this._command("sendMessage", args);
    }

    async editMessageText(chat_id: number, message_id: number, text: string) {
        return await this._command("editMessageText", {
            chat_id,
            message_id,
            text,
        });
    }

    async sendPhoto(chat_id: number, photo: string, reply_markup?: InlineKeyboardMarkup) {
        return await this._command("sendPhoto", {
            chat_id,
            photo,
            reply_markup,
        });
    }

    async sendAudio(chat_id: number, audio: string, reply_markup?: InlineKeyboardMarkup) {
        return await this._command("sendAudio", {
            chat_id,
            audio,
            reply_markup,
        });
    }

    async getFile(file_id: string): Promise<File> {
        return await this._command("getFile", { file_id });
    }

    async setWebhook(url: string) {
        return await this._command("setWebhook", { url });
    }

    async deleteWebhook() {
        return await this._command("deleteWebhook");
    }

    async getWebhookInfo() {
        return (await this._command("getWebhookInfo")) as Promise<WebhookInfo>;
    }

    async setMyCommands(commands: BotCommand[]) {
        return await this._command("setMyCommands", { commands });
    }

    async setMessageReaction(chat_id: number, message_id: number, reaction: string, big = false) {
        return await this._command("setMessageReaction", {
            chat_id,
            message_id: message_id,
            reaction: [{ type: "emoji", emoji: reaction }],
            is_big: big,
        });
    }

    async setChatMenuButton(url?: string) {
        return await this._command("setChatMenuButton", {
            menu_button: url
                ? {
                      type: "web_app",
                      text: "Application",
                      web_app: { url: "https://" + url + "/site" },
                  }
                : { type: "default" },
        });
    }

    async getMe() {
        return await this._command("getMe");
    }

    async getChat(chat_id: string) {
        return await this._command("getChat", { chat_id });
    }

    async _command(cmd: string, data?: Record<string, unknown>) {
        const url = `${Telegram.API}/bot${this.token}/${cmd}`;
        console.log("TELEGRAM REQUEST", url, data || "");
        try {
            let response: Response;
            if (data) {
                response = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
            } else response = await fetch(url);
            if (!response.ok) {
                const msg = `error: ${response.status} ${response.statusText}`;
                throw new Error(msg);
            }
            const result = await response.json();
            if (!result.ok) {
                console.error("TELEGRAM ERROR", result);
                const msg = `${result.error_code} ${result.description || ""}`;
                throw new Error(msg);
            }
            return result.result;
        } catch (e: unknown) {
            console.error("TELEGRAM ERROR", url, data);
            if (e instanceof Error) console.error("ERROR", e.message);
            else console.error("ERROR", e);
        }
    }
}

// #endregion

// #region listener
export function listener() {
    const port = Number(env.PORT || 8000);
    Deno.serve({ port, handler, onListen: () => console.log(`listening port ${port}`) });
    console.log("listener started");
}
// #endregion

async function process_message(message: Message) {
    const { chat, message_id, text: text_, web_app_data } = message;

    const text = text_ || web_app_data?.data;

    if (text?.includes("?")) {
        await telegram.sendMessage(chat.id, "ha? " + (text ? text : ""), {
            reply_parameters: { message_id: message_id },
        });
    } else {
        await telegram.sendMessage(chat.id, "> " + (text ? text : ""), {
            reply_markup: {
                keyboard: [[{ text: "Application", web_app: { url: "https://" + TunnelURL + "/site" } }]],
                one_time_keyboard: true,
                resize_keyboard: true,
            },
        });
    }
}

async function handler(req: Request) {
    const { pathname } = new URL(req.url);

    if (pathname === "/health") return Response.json({ status: "alive" });
    if (pathname === "/wh") return Response.json({ url: (await telegram.getWebhookInfo()).url });
    if (pathname === "/bot") {
        const update = (await req.json()) as Update;
        console.log({ update });
        const { message } = update;
        if (message) await process_message(message);
        return new Response(null, { status: 200 });
    }
    if (pathname.startsWith("/site")) {
        return serveDir(req, {
            fsRoot: ".",
        });
    }

    return new Response("ha?", { status: 404 });
}

// #region tunnel
async function tunnel() {
    consola.info("ngrok", { version: ngrok.version() });
    const host = (await ngrok.connect({ protocol: "http", port: 8000 }).next()).value;
    if (!host) consola.fatal("tunnel host is undefined"), process.exit(1);
    return host;
}
// #endregion

// #region
export async function installWebhook(host: string) {
    const webhook = `https://${host}/bot`;

    if (host.includes(".dev")) {
        if (!(await consola.prompt(`install webhook? [${webhook}]`, { type: "confirm" }))) process.exit(0);
    }

    console.info("install webhook", { webhook: webhook });
    if (!(await telegram.setWebhook(webhook))) consola.fatal("setWebhook failed"), process.exit(1);

    return host;
}
// #endregion

// #region health
export async function health(host: string) {
    try {
        const url = `https://${host}/health`;
        consola.info("health", { url });
        const health = await (await fetch(url)).json();
        console.log(health);
    } catch (_e) {
        consola.error("health check failed", { host });
    }
}
// #endregion

// #region ngrok
import { mergeReadableStreams } from "@std/streams/merge-readable-streams";
import { TextLineStream } from "@std/streams/text-line-stream";

// deno-lint-ignore no-namespace
namespace ngrok {
    export type NgrokOptions = { protocol: string; port: number };

    export function version() {
        const process = new Deno.Command("ngrok", {
            args: ["version"],
            stdout: "piped",
            stderr: "piped",
        }).outputSync();
        return new TextDecoder().decode(process.stdout).trim();
    }

    export async function* connect(options: NgrokOptions) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const process = new Deno.Command("ngrok", {
            args: [options.protocol, options.port.toString(), "--log=stdout"],
            stdin: "piped",
            stdout: "piped",
            stderr: "piped",
        }).spawn();
        process.stdin?.close();

        const output = mergeReadableStreams(process.stdout, process.stderr)
            .pipeThrough(new TextDecoderStream())
            .pipeThrough(new TextLineStream());

        const ready = /started tunnel.*:\/\/(.*)/;
        for await (const line of output) {
            if (env.VERBOSE) console.log("ngrok |", line);
            const connected = line.match(ready);
            if (connected) {
                const url = connected[1];
                console.log("ngrok connected", { url });
                yield connected[1];
            }
        }
        console.log("ngrok exited");
    }
}
// #endregion

// #region main
const { BOT_TOKEN } = env;
if (!BOT_TOKEN) consola.fatal("BOT_TOKEN is not set"), process.exit(1);

const telegram = new Telegram(BOT_TOKEN);

const { id, first_name, username } = await telegram.getMe();
console.dir({ id, first_name, username });

// #region commands

// #region flags
const FLAGS = {
    "--tunnel": "ngrok tunnel",
    "--webhook:install": "install webhook",
    "--webhook:delete": "delete webhook",
    "--webhook:info": "get webhook info",
    "--dev": "establish tunnel, install webhook and run listener",
    "--help": "show help",
} as const;
const flags = Object.fromEntries(
    Object.keys(FLAGS).map((flag) => {
        const i = argv.indexOf(flag);
        const arg = i > -1 ? argv.slice(i + 1) : undefined;
        return [flag, arg];
    })
);
// #endregion
if (flags["--help"]) {
    Object.entries(FLAGS).forEach(([flag, desc]) => console.log(flag, "-", desc));
    process.exit(0);
} else if (argv.includes("--tunnel")) {
    consola.info({ tunnel: await tunnel() });
} else if (argv.includes("--webhook:install")) {
    const { DENO_HOST } = env;
    if (!DENO_HOST) consola.fatal("DENO_HOST is not set"), process.exit(1);
    const host = await installWebhook(DENO_HOST);
    await health(host);
    process.exit(0);
} else if (argv.includes("--webhook:delete")) {
    if (!(await consola.prompt(`delete webhook?`, { type: "confirm" }))) process.exit(0);
    await telegram.deleteWebhook();
    consola.info("webhook deleted");
    consola.info(await telegram.getWebhookInfo());
    process.exit(0);
} else if (argv.includes("--webhook:info")) {
    consola.info(await telegram.getWebhookInfo());
    process.exit(0);
} else if (argv.includes("--dev")) {
    listener();

    const tunnelURL = await tunnel();
    consola.info({ tunnel: tunnelURL });
    if (!tunnelURL) consola.fatal("tunnel URL is undefined"), process.exit(1);
    consola.info("install webhook", { tunnelURL });
    const host = await installWebhook(tunnelURL);
    await health(host);

    TunnelURL = tunnelURL;
    await telegram.setMyCommands([{ command: "refresh", description: "Refresh" }]);
    await telegram.setChatMenuButton(TunnelURL);
} else {
    listener();
}
// #endregion
