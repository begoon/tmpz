import { auth } from "@googleapis/gmail";

export const ENV_FILE = ".env";

// Sending only: this scope cannot read, list or delete mail.
export const SCOPES = ["https://www.googleapis.com/auth/gmail.send"];

export function requireEnv(name: string): string {
    const value = process.env[name];
    if (!value) {
        throw new Error(`${name} is not set. Add it to ${ENV_FILE} (see .env.example).`);
    }
    return value;
}

export function createOAuthClient(redirectUri?: string) {
    return new auth.OAuth2({
        clientId: requireEnv("GOOGLE_CLIENT_ID"),
        clientSecret: requireEnv("GOOGLE_CLIENT_SECRET"),
        redirectUri,
    });
}
