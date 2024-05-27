import { load } from "https://deno.land/std@0.211.0/dotenv/mod.ts";
import { installWebhook } from "./wh.ts";

await load({ envPath: `./.env-hosting`, export: true });

const HOSTING = Deno.env.get("HOSTING");
if (!HOSTING) throw new Error("HOSTING is not set");

const url = HOSTING + "/bot";
await installWebhook(url);
