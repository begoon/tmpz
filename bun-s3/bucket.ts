import { env } from "node:process";

const { S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_REGION, S3_BUCKET } = env;

const client = new Bun.S3Client({
    bucket: S3_BUCKET,
    region: S3_REGION,
    endpoint: "https://storage.googleapis.com",
    accessKeyId: S3_ACCESS_KEY_ID,
    secretAccessKey: S3_SECRET_ACCESS_KEY,
});

const f = client.file("gallery.gal");
console.log((await f.arrayBuffer()).byteLength);
