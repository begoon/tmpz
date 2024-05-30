import type {
    BotCommand,
    File,
    InlineKeyboardMarkup,
    ParseMode,
} from "npm:@types/node-telegram-bot-api";

const api = "https://api.telegram.org";

import { nice } from "./pprint.ts";

const nicer = (v: unknown) => (v ? nice(v) : "");

export class Telegram {
    token: string;

    constructor(token: string) {
        this.token = token;
    }

    file(path: string) {
        return `${api}/file/bot${this.token}/${path}`;
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
        reply_markup?: InlineKeyboardMarkup,
        parse_mode?: ParseMode
    ) {
        return await this._command("sendMessage", {
            chat_id,
            text,
            reply_markup,
            parse_mode,
        });
    }

    async editMessageText(chat_id: number, message_id: number, text: string) {
        return await this._command("editMessageText", {
            chat_id,
            message_id,
            text,
        });
    }

    async sendPhoto(
        chat_id: number,
        photo: string,
        reply_markup?: InlineKeyboardMarkup
    ) {
        return await this._command("sendPhoto", {
            chat_id,
            photo,
            reply_markup,
        });
    }

    async sendAudio(
        chat_id: number,
        audio: string,
        reply_markup?: InlineKeyboardMarkup
    ) {
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
        return await this._command("setWebhook", {
            url,
            drop_pending_updates: true,
        });
    }

    async deleteWebhook() {
        return await this._command("deleteWebhook");
    }

    async getWebhookInfo() {
        return await this._command("getWebhookInfo");
    }

    async setMyCommands(commands: BotCommand[]) {
        return await this._command("setMyCommands", { commands });
    }

    async _command(cmd: string, data?: Record<string, unknown>) {
        const url = `${api}/bot${this.token}/${cmd}`;
        // deno-lint-ignore no-constant-condition
        if (false) console.log("TELEGRAM REQUEST", url, nicer(data));
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
                console.error("TELEGRAM ERROR", nicer(result));
                const msg = `${result.error_code} ${result.description || ""}`;
                throw new Error(msg);
            }
            return result.result;
        } catch (e: unknown) {
            console.error("TELEGRAM REQUEST", url, nicer(data));
            if (e instanceof Error) console.error("ERROR", e.message);
            else console.error("ERROR", e);
        }
    }
}
