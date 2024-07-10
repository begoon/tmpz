import { Firestore } from "@google-cloud/firestore";
import { GoogleAuth } from "google-auth-library";

import { Buffer } from "node:buffer";
import { env } from "node:process";

const key = Buffer.from(env.GCLOUND_CREDENTIALS_BASE64!, "base64").toString();
const credentials = JSON.parse(key);

const auth = new GoogleAuth({ credentials: credentials });

const firestore = new Firestore({ authClient: await auth.getClient() });

const document = firestore.collection("karta").doc("wheel");

await document.set({
    title: "title",
    body: "message",
    when: new Date().toISOString(),
});

const read = await document.get();
console.log("read", read.data());

// await document.delete();
