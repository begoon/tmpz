# reactor

A separate Discord application using Bun and HTTP interaction callbacks. `/info` replies with the running Bun version and current date/time in UTC. `/me` replies `I am Reactor`. No Gateway connection, Docker container, or daemon is needed.

Production: https://reactor-green.vercel.app. Discord's configured callback is `https://reactor-green.vercel.app/interactions`; `/health` reports the runtime and configuration status. The Vercel project is `me-default/reactor`, deployed separately from notifier. `/info` and `/me` are registered in Operations.

Discord POSTs to `/interactions`. The handler verifies the Ed25519 signature against the original request body, rejects timestamps older than five minutes, answers Discord's endpoint verification PING, and returns command responses directly as JSON.

## Setup

1. Create a **new application named reactor** in the [Discord Developer Portal](https://discord.com/developers/applications). Do not reuse notifier: interaction delivery is configured per application.
2. Copy `reactor/.env.example` to `reactor/.env`. Set Application ID and Public Key from General Information, and the token from the Bot page. Keep the Operations guild ID already in the template.
3. Under Installation, configure Guild Install with `bot` and `applications.commands` scopes, then install reactor in Operations. No Message Content Intent is needed.
4. From this folder, run `bun install`, then `just check`. `just dev` serves locally on port 3001.
5. Link this folder to a separate Vercel project. Set `DISCORD_PUBLIC_KEY`, `DISCORD_APPLICATION_ID`, and `DISCORD_GUILD_ID` in its production environment, then run `just deploy`. Runtime does not need the bot token.
6. Set the application's **Interactions Endpoint URL** to `https://YOUR-PRODUCTION-DOMAIN/interactions`. The URL must be publicly reachable without Vercel authentication. Discord validates it before saving.
7. Run `just register` from this folder to register `/info` and `/me` in Operations, then use `/info` in Discord.

Run all reactor commands from this directory so its credentials are loaded. `.env` is ignored by Git and excluded from deployment. The health endpoint reports whether runtime configuration is present; a healthy HTTP endpoint alone does not confirm Discord installation.

Reference: [Discord HTTP interactions](https://docs.discord.com/developers/interactions/receiving-and-responding).
