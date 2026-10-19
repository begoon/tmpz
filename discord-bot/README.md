# Discord bots

Two Bun bots for the Operations Discord server, each with its own Discord application and Vercel deployment:

- [Notifier](notifier/README.md) receives messages and slash commands over a persistent Discord Gateway WebSocket connection. Runs as a Vercel daemon.
- [Reactor](reactor/README.md) receives slash commands through signed HTTP callbacks. Runs as a Vercel Bun function.

Run setup, development, checks, and deployment commands from the relevant bot directory (`cd notifier` or `cd reactor`). Each folder contains its own README, Justfile, dependencies, environment configuration, and Vercel project link.
