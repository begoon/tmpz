import "https://deno.land/std@0.211.0/dotenv/load.ts";

import { connect } from "./ngrok/ngrok.ts";
import { installWebhook } from "./wh.ts";

const host = (await connect({ protocol: "http", port: 8000 }).next()).value;

const url = `https://${host}/bot`;
console.log({ tunnel: url });

await installWebhook(url);
