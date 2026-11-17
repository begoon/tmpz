// Sends a plain-text email through the Gmail API.
//
//   bun run src/send.ts --to someone@example.com --subject "Hi" --body "Hello"

import { parseArgs } from "node:util";
import { gmail } from "@googleapis/gmail";
import { createOAuthClient, requireEnv } from "./config";

const USAGE = 'Usage: bun run src/send.ts --to <address> --subject "<subject>" --body "<text>"';

function parseOptions() {
    const { values } = parseArgs({
        args: Bun.argv.slice(2),
        options: {
            to: { type: "string" },
            subject: { type: "string" },
            body: { type: "string" },
            help: { type: "boolean", short: "h" },
        },
        strict: true,
    });
    if (values.help) {
        console.log(USAGE);
        process.exit(0);
    }
    const { to, subject, body } = values;
    if (!to || subject === undefined || body === undefined) {
        throw new Error(`--to, --subject and --body are all required.\n${USAGE}`);
    }
    // A line break in a header value would let the caller inject extra headers.
    if (/[\r\n]/.test(to) || /[\r\n]/.test(subject)) {
        throw new Error("--to and --subject must not contain line breaks.");
    }
    return { to, subject, body };
}

function base64(text: string): string {
    return Buffer.from(text, "utf8").toString("base64");
}

// RFC 2047 encoded-word, so non-ASCII subjects survive.
function encodeHeader(text: string): string {
    return /^[\x20-\x7e]*$/.test(text) ? text : `=?UTF-8?B?${base64(text)}?=`;
}

function buildRawMessage(to: string, subject: string, body: string): string {
    const encodedBody = base64(body).replace(/(.{76})/g, "$1\r\n");
    const message = [
        `To: ${to}`,
        `Subject: ${encodeHeader(subject)}`,
        "MIME-Version: 1.0",
        'Content-Type: text/plain; charset="UTF-8"',
        "Content-Transfer-Encoding: base64",
        "",
        encodedBody,
    ].join("\r\n");
    return Buffer.from(message, "utf8").toString("base64url");
}

async function main() {
    const { to, subject, body } = parseOptions();

    // The client exchanges the refresh token for a short-lived access token
    // on the first request and attaches it as a Bearer header.
    const client = createOAuthClient();
    client.setCredentials({ refresh_token: requireEnv("GOOGLE_REFRESH_TOKEN") });

    const response = await gmail({ version: "v1", auth: client }).users.messages.send({
        userId: "me",
        requestBody: { raw: buildRawMessage(to, subject, body) },
    });

    console.log(`Sent to ${to}. Message id: ${response.data.id}`);
}

main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
});
