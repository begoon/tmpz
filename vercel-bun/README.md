# Bun on Vercel

A minimal `Bun.serve()` example with no dependencies.

- `/health` returns `ok` as plain text.
- `/ws` replies to `ping` with `pong` and reverses all other messages.
- `/` serves `index.html` with an inline JavaScript WebSocket client. Send with Enter or the Send button.

Run locally with `bun run dev`, then open http://localhost:3000.
Run `bun run verify` while the server is running to check HTTP routes and
WebSocket replies. Pass a deployed URL to check production:
`bun run verify https://your-project.vercel.app`.

Deploy with `vercel --prod`. The Bun framework preset detects `server.ts`;
`vercel.json` enables the Bun runtime.

Based on https://vercel.com/changelog/bun-serve-entrypoint-for-vercel-functions.
