// One-off interactive login: opens the Google consent screen, receives the
// authorization code on a local loopback server, exchanges it for tokens and
// stores the refresh token in .env.

import { CodeChallengeMethod } from "google-auth-library";
import { ENV_FILE, SCOPES, createOAuthClient } from "./config";

const TIMEOUT_MS = 5 * 60 * 1000;

async function saveEnvValue(name: string, value: string) {
    const file = Bun.file(ENV_FILE);
    const text = (await file.exists()) ? await file.text() : "";
    const line = `${name}=${value}`;
    const pattern = new RegExp(`^${name}=.*$`, "m");
    const updated = pattern.test(text)
        ? text.replace(pattern, () => line)
        : `${text}${text === "" || text.endsWith("\n") ? "" : "\n"}${line}\n`;
    await Bun.write(ENV_FILE, updated);
}

async function main() {
    const state = crypto.randomUUID();
    const { promise: codePromise, resolve, reject } = Promise.withResolvers<string>();

    const server = Bun.serve({
        hostname: "127.0.0.1",
        port: 0,
        fetch(request) {
            const url = new URL(request.url);
            if (url.pathname !== "/oauth2callback") {
                return new Response("Not found", { status: 404 });
            }
            const error = url.searchParams.get("error");
            const code = url.searchParams.get("code");
            if (error) {
                reject(new Error(`Google returned an error: ${error}`));
                return new Response(`Authorization failed: ${error}`, { status: 400 });
            }
            if (!code || url.searchParams.get("state") !== state) {
                reject(new Error("Callback had no code or a mismatched state."));
                return new Response("Invalid callback.", { status: 400 });
            }
            resolve(code);
            return new Response("Authorized. You can close this tab and return to the terminal.");
        },
    });

    const redirectUri = `http://127.0.0.1:${server.port}/oauth2callback`;
    const client = createOAuthClient(redirectUri);
    const { codeVerifier, codeChallenge } = await client.generateCodeVerifierAsync();

    const authUrl = client.generateAuthUrl({
        access_type: "offline", // ask for a refresh token
        prompt: "consent", // force Google to issue a refresh token every time
        scope: SCOPES,
        state,
        code_challenge: codeChallenge,
        code_challenge_method: CodeChallengeMethod.S256,
    });

    console.log(`Open this URL in your browser to authorize:\n\n${authUrl}\n`);
    Bun.spawn(["open", authUrl], { stdout: "ignore", stderr: "ignore" });

    const timer = setTimeout(() => reject(new Error("Timed out waiting for authorization.")), TIMEOUT_MS);
    try {
        const code = await codePromise;
        const { tokens } = await client.getToken({ code, codeVerifier, redirect_uri: redirectUri });
        if (!tokens.refresh_token) {
            throw new Error("Google did not return a refresh token.");
        }
        await saveEnvValue("GOOGLE_REFRESH_TOKEN", tokens.refresh_token);
        console.log(`Refresh token saved to ${ENV_FILE} as GOOGLE_REFRESH_TOKEN.`);
    } finally {
        clearTimeout(timer);
        await server.stop();
    }
}

main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
});
