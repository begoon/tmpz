import { KeyManagementServiceClient } from "@google-cloud/kms";
import { OAuth2Client } from "google-auth-library";
import fs from "node:fs";

const { PROFILE_META_KEY } = process.env;
console.log(PROFILE_META_KEY);

async function main() {
    const access_token = process.env.GOOGLE_ACCESS_TOKEN;

    const authClient = new OAuth2Client({ credentials: { access_token } });

    const kms = new KeyManagementServiceClient({ authClient });

    const base64 = fs.readFileSync("encrypted_key.txt", "utf-8");
    const ciphertext = Buffer.from(base64, "base64");

    const [result] = await kms.decrypt({ name: PROFILE_META_KEY, ciphertext });
    console.log(result);
    if (!(result.plaintext instanceof Uint8Array)) {
        console.error("result is not a Uint8Array");
        return;
    }
    console.log(toHex(result.plaintext));
}

function toHex(v: Uint8Array) {
    return Array.from(v)
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
}

await main();
