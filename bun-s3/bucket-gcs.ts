import { createHash, createHmac } from "node:crypto";
import { env } from "node:process";

const { GCS_ACCESS_KEY, GCS_SECRET_KEY, GCS_REGION, GCS_BUCKET } = env;

const host = "storage.googleapis.com";

// -- list bucket via S3 REST API (Bun's S3 client has no list method) --

function hmac(key: Buffer | string, data: string): Buffer {
    return createHmac("sha256", key).update(data).digest();
}

function sha256(data: string): string {
    return createHash("sha256").update(data).digest("hex");
}

const method = "GET";
const path = `/${GCS_BUCKET}`;
const now = new Date();
const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, "");
const dateStamp = amzDate.slice(0, 8);

const queryParams = new URLSearchParams({ "list-type": "2" });
queryParams.sort();
const queryString = queryParams.toString();

const payloadHash = sha256("");
const headers: Record<string, string> = {
    host,
    "x-amz-content-sha256": payloadHash,
    "x-amz-date": amzDate,
};

const signedHeaderKeys = Object.keys(headers).sort();
const signedHeaders = signedHeaderKeys.join(";");
const canonicalHeaders = signedHeaderKeys.map((k) => `${k}:${headers[k]}\n`).join("");

const canonicalRequest = [method, path, queryString, canonicalHeaders, signedHeaders, payloadHash].join("\n");

const credentialScope = `${dateStamp}/${GCS_REGION}/s3/aws4_request`;
const stringToSign = ["AWS4-HMAC-SHA256", amzDate, credentialScope, sha256(canonicalRequest)].join("\n");

const signingKey = hmac(hmac(hmac(hmac(`AWS4${GCS_SECRET_KEY}`, dateStamp), GCS_REGION!), "s3"), "aws4_request");
const signature = hmac(signingKey, stringToSign).toString("hex");

const authorization = `AWS4-HMAC-SHA256 Credential=${GCS_ACCESS_KEY}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

const response = await fetch(`https://${host}${path}?${queryString}`, {
    method,
    headers: { ...headers, Authorization: authorization },
});

if (!response.ok) {
    console.error(`error ${response.status}: ${await response.text()}`);
    process.exit(1);
}

const xml = await response.text();
const keys = [...xml.matchAll(/<Key>([^<]+)<\/Key>/g)].map((m) => m[1]);
console.log(`found ${keys.length} objects in bucket "${GCS_BUCKET}":`);
for (const key of keys) {
    console.log(`  ${key}`);
}

// -- read a file using Bun's S3 client --

const client = new Bun.S3Client({
    bucket: GCS_BUCKET,
    region: GCS_REGION,
    endpoint: `https://${host}`,
    accessKeyId: GCS_ACCESS_KEY,
    secretAccessKey: GCS_SECRET_KEY,
});

const f = client.file("bot_package.zip");
console.log(`\nbot_package.zip size: ${(await f.arrayBuffer()).byteLength} bytes`);
