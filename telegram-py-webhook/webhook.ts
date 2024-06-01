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
if (!env) {
    throw new Error("missing hosting: " + Object.keys(envs).join(" | "));
}

const HOSTING = Deno.env.get(envs[env]);
if (!HOSTING) throw new Error(envs[env] + " is not set");

await installWebhook(HOSTING);
