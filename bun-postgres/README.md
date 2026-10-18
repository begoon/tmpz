# Bun Postgres

A small PostgreSQL workspace built with Bun's native `SQL` client and vendored htmx 2.0.8. No frontend framework or production npm dependencies.

## Run locally

```sh
bun install
cp .env.example .env # only for a fresh checkout; keep your existing .env
bun dev
```

Open http://localhost:3000. Bun loads `.env` automatically. Set `DATABASE_URI` to your PostgreSQL connection string (`DATABASE_URL` is also supported). TLS settings can be included in the connection URL.

When `ADMIN_PASSWORD` is set, sign in with username `admin` and that password. Production refuses unauthenticated access and requires this variable. This deployment's generated password is stored in your local `.env`.

## Features

- Browse tables in the `public` schema, 50 rows per page.
- Create tables with typed columns, composite primary keys, required columns, and integer identity columns.
- Drop tables with confirmation; dependent objects prevent the drop (no cascade).
- Insert rows with distinct value, SQL NULL, and default/omitted modes. Empty strings are supported.
- Delete individual rows, including rows without a primary key. PostgreSQL `ctid`, `xmin`, and `tableoid` prevent deletion of rows changed since they were displayed.
- Execute SQL in a transaction with a 10-second statement timeout. Results display up to 500 rows; use LIMIT in large SELECT queries to bound database/network work. Commands that cannot run within a transaction, such as VACUUM, are not supported. Use one statement per execution.
- Responsive UI, escaped database output, same-origin write validation, and HTTP Basic authentication.

The SQL editor has the privileges of the configured database account. All database operations run server-side. Connection strings never reach browser code. Table browsing preserves PostgreSQL text representations of large integers, dates, and JSON.

## Verify

```sh
bun run check
bun test
INTEGRATION=1 bun test
```

The integration test creates and removes its own uniquely named table using the configured connection.

## Deploy

The project uses the [Vercel Bun framework preset](https://vercel.com/docs/functions/runtimes/bun), with `bunVersion: "1.4.x"` and `server.ts` as its entrypoint.

```sh
vercel link
vercel env add DATABASE_URI production --sensitive
vercel env add ADMIN_PASSWORD production --sensitive
vercel deploy --prod
```

Enter secrets through the CLI prompt, not command-line arguments. Set both variables for preview deployments if needed. `.env` files are excluded from source uploads. The local htmx library and license are under `public/vendor/`; browser requests do not depend on a CDN.

After editing files in `public/`, run `bun run assets` to regenerate the embedded server assets. The development and Vercel build commands do this automatically.
