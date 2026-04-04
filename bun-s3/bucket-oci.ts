import { createHash, createHmac } from "node:crypto";
import { env } from "node:process";

const { OCI_ACCESS_KEY, OCI_SECRET_KEY, OCI_REGION, OCI_BUCKET_NAMESPACE, OCI_BUCKET_NAME } = env;

const host = `${OCI_BUCKET_NAMESPACE}.compat.objectstorage.${OCI_REGION}.oraclecloud.com`;

function hmac(key: Buffer | string, data: string): Buffer {
    return createHmac("sha256", key).update(data).digest();
}

function sha256(data: string): string {
    return createHash("sha256").update(data).digest("hex");
}

const method = "GET";
const path = `/${OCI_BUCKET_NAME}`;
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

const credentialScope = `${dateStamp}/${OCI_REGION}/s3/aws4_request`;
const stringToSign = ["AWS4-HMAC-SHA256", amzDate, credentialScope, sha256(canonicalRequest)].join("\n");

const signingKey = hmac(hmac(hmac(hmac(`AWS4${OCI_SECRET_KEY}`, dateStamp), OCI_REGION!), "s3"), "aws4_request");
const signature = hmac(signingKey, stringToSign).toString("hex");

const authorization = `AWS4-HMAC-SHA256 Credential=${OCI_ACCESS_KEY}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

const url = `https://${host}${path}?${queryString}`;
const headers_ = { ...headers, Authorization: authorization };

console.log(`making request to [${url}] with headers:`, headers_);

const response = await fetch(url, { method, headers: headers_ });

if (!response.ok) {
    console.error(`error ${response.status}: ${await response.text()}`);
    process.exit(1);
}

const xml = await response.text();
const keys = [...xml.matchAll(/<Key>([^<]+)<\/Key>/g)].map((m) => m[1]);
console.log(`found ${keys.length} objects in bucket "${OCI_BUCKET_NAME}":`);
for (const key of keys) {
    console.log(`  ${key}`);
}

// Read a file using Bun's S3 client
const client = new Bun.S3Client({
    bucket: OCI_BUCKET_NAME,
    region: OCI_REGION,
    endpoint: `https://${host}`,
    accessKeyId: OCI_ACCESS_KEY,
    secretAccessKey: OCI_SECRET_KEY,
});

const f = client.file("abc.pdf");
console.log(`\nabc.pdf size: ${(await f.arrayBuffer()).byteLength} bytes`);
