#!/usr/bin/env bun
// Logs a structured entry to GCP Cloud Logging.
//
// Uses the REST API (entries:write) directly via fetch — the
// @google-cloud/logging SDK's transport hangs under Bun.
//
// Usage:
//   bun run gcp-message.ts [options] <message...>
//
// Options:
//   --project <id>    GCP project id (default: $GOOGLE_CLOUD_PROJECT or ADC default)
//   --log <name>      Log name (default: gcp-message)
//   --severity <sev>  DEFAULT|DEBUG|INFO|NOTICE|WARNING|ERROR|CRITICAL (default: INFO)
//
// Auth: uses Application Default Credentials (`gcloud auth application-default login`).
//
// Example:
//   bun run gcp-message.ts --project iproov-chiro "slack: deployment failed"

import { hostname } from "node:os";
import { GoogleAuth } from "google-auth-library";

interface Options {
  project?: string;
  log: string;
  severity: string;
  message: string;
}

function usage(): never {
  console.error(
    "Usage: bun run gcp-message.ts [--project <id>] [--log <name>] [--severity <sev>] <message...>",
  );
  process.exit(1);
}

function parseArgs(argv: string[]): Options {
  const opts: Options = {
    project: process.env.GOOGLE_CLOUD_PROJECT,
    log: "gcp-message",
    severity: "INFO",
    message: "",
  };
  const words: string[] = [];

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "--project":
        opts.project = argv[++i] ?? usage();
        break;
      case "--log":
        opts.log = argv[++i] ?? usage();
        break;
      case "--severity":
        opts.severity = (argv[++i] ?? usage()).toUpperCase();
        break;
      case "--help":
      case "-h":
        usage();
      default:
        words.push(arg);
    }
  }

  opts.message = words.join(" ").trim();
  if (!opts.message) usage();
  return opts;
}

const opts = parseArgs(process.argv.slice(2));

const auth = new GoogleAuth({
  scopes: ["https://www.googleapis.com/auth/logging.write"],
});
const projectId = opts.project ?? (await auth.getProjectId());
const token = await (await auth.getClient()).getAccessToken();
if (!token.token) throw new Error("Failed to obtain access token from ADC");

const logName = `projects/${projectId}/logs/${encodeURIComponent(opts.log)}`;

const response = await fetch("https://logging.googleapis.com/v2/entries:write", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token.token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    entries: [
      {
        logName,
        resource: { type: "global", labels: { project_id: projectId } },
        severity: opts.severity,
        jsonPayload: {
          message: opts.message,
          source: "gcp-message.ts",
          hostname: hostname(),
        },
      },
    ],
  }),
});

if (!response.ok) {
  console.error(`entries:write failed (HTTP ${response.status}): ${await response.text()}`);
  process.exit(1);
}

console.log(`Logged to ${logName} [${opts.severity}]: ${opts.message}`);
process.exit(0);
