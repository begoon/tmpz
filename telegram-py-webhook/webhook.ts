import { load } from "https://deno.land/std@0.211.0/dotenv/mod.ts";
import { deleteWebhook, installWebhook, webhookInfo } from "./wh.ts";

await load({ envPath: `./.env`, export: true });

if (Deno.args.includes("--delete")) {
    await deleteWebhook();
    Deno.exit(0);
}

if (Deno.args.includes("--info")) {
    await webhookInfo();
    Deno.exit(0);
}

const envs: Record<string, string> = {
    aws: "AWS_HOSTING",
    gcp: "GCP_HOSTING",
    az: "AZ_HOSTING",
};

const env = Deno.args[0];
const HOSTING = Deno.env.get(envs[env]);

if (!HOSTING) throw new Error("HOSTING is not set");

const url = HOSTING;
await installWebhook(url);
