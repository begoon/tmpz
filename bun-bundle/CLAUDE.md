Default to using Bun instead of Node.js.

- Use `bun <file>` instead of `node <file>` or `ts-node <file>`
- Use `bun test` instead of `jest` or `vitest`
- Use `bun build <file.html|file.ts|file.css>` instead of `webpack` or `esbuild`
- Use `bun install` instead of `npm install` or `yarn install` or `pnpm install`
- Use `bun run <script>` instead of `npm run <script>` or `yarn run <script>` or `pnpm run <script>`
- Use `bunx <package> <command>` instead of `npx <package> <command>`
- Bun automatically loads .env, so don't use dotenv.

## Project structure

- `index.ts` — web server using `Bun.serve()`, serves static files from `static/` and `/version` API endpoint
- `static/` — static assets, embedded into the compiled binary via `Bun.embeddedFiles`
- `Dockerfile` — multi-stage build: compiles to single executable with `bun build --compile` (musl target), final image is `FROM scratch` with only the binary and musl/libstdc++/libgcc libs
- `Justfile` — build recipes: `build-linux`, `build-macos`, `docker-build`, `docker-run`

## Build & run

- `bun run index.ts` — run the server locally (serves from `static/` directory)
- `just build-macos` — compile single executable for macOS
- `just build-linux` — compile single executable for Linux (x64, musl)
- `just docker-build` — build Docker image (linux/amd64, FROM scratch)
- `just docker-run` — run Docker container (`--init` for signal handling)

## Embedding static files

Static files are passed to the build command as extra entrypoints:

```sh
bun build --compile ./index.ts $(find static -type f) --outfile exe
```

At runtime, `Bun.embeddedFiles` provides the embedded blobs. The `fetch` handler serves them by matching the pathname. In dev mode (not compiled), it falls back to reading from `static/` on disk.

Note: `Bun.serve()` `static` property cannot be combined with `routes` — use the `fetch` fallback instead.

## APIs

- `Bun.serve()` supports WebSockets, HTTPS, and routes. Don't use `express`.
- `bun:sqlite` for SQLite. Don't use `better-sqlite3`.
- `Bun.redis` for Redis. Don't use `ioredis`.
- `Bun.sql` for Postgres. Don't use `pg` or `postgres.js`.
- `WebSocket` is built-in. Don't use `ws`.
- Prefer `Bun.file` over `node:fs`'s readFile/writeFile
- Bun.$`ls` instead of execa.

## Testing

Use `bun test` to run tests.

For more information, read the Bun API docs in `node_modules/bun-types/docs/**.mdx`.
