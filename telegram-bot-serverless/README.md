# Telegram Serverless example

A notes bot and Mini App running directly on [Telegram Serverless](https://core.telegram.org/bots/serverless), with command handlers, inline callback buttons, an authenticated web interface, and Telegram's persistent SQLite database. No web server, polling loop, external database, or hosting account is needed.

## Run locally and deploy

Use Node.js 24 or newer (local scripts and tests). The deployed code is plain JavaScript using Telegram's SDK.

```sh
npm install
npm test
```

With [just](https://github.com/casey/just) installed, run `just` to list tasks:

```sh
just install       # install locked dependencies
just build         # validate JavaScript syntax (no bundling needed)
just test          # local handler and SQLite tests
just check         # build + test
just deploy        # check, upload, safe migrations, webhook sync, command menu
just status        # local changes vs. the last cloud snapshot
just webhook       # inspect delivery health
just migrate-plan  # preview database changes
just bot-check     # verify the Bot API token
```

`just deploy` needs both tokens configured as described below. For code-only
uploads use `just push`. Other tasks include `init`, `fetch`, `diff`, `migrate`,
`webhook-sync`, `setup`, and `cloud` for arbitrary CLI commands. No task loads
`.env` through the shell; the Node scripts load it without printing secrets.

Keep the existing `BOT_TOKEN` in `.env`. **Deployment requires a different token:** enable Serverless in BotFather → your bot → Serverless, then copy CLI Access → Access token. Add it to `.env`:

```dotenv
BOT_TOKEN=your-existing-bot-api-token
TGCLOUD_TOKEN=app123:your-serverless-access-token
```

Alternatively, run `npm run cloud -- login` to save the CLI token interactively. `.env` and `.tgcloud/` are ignored by Git. Tokens are never embedded in deployed code; Telegram authenticates `sdk.api` itself.

For a fresh clone, initialize the CLI's local state first:

```sh
npm run cloud -- init
npm run status
npm run deploy
npm run migrate -- --safe
npm run cloud -- webhook sync
npm run setup
```

`deploy` uploads code and the `webapp/` static files; `migrate` creates database tables separately. Complete both before trying database commands. `--safe` only applies safe schema changes. `setup` registers the command menu and **My notes** Mini App menu button using `BOT_TOKEN`; `npm run setup -- --check` only verifies the token. The app URL is derived from `TGCLOUD_TOKEN`. If you use CLI login instead, set `MINI_APP_URL` in `.env` to the URL printed by deployment. The `npm run cloud` wrapper loads `.env`; bare `npx tgcloud` does not load it for you.

## Try it in Telegram

1. Send `/start` or `/help` for command examples.
2. Send `/add Buy milk` to insert a note.
3. Send `/notes` to select your ten newest notes.
4. Tap **Complete**, **Reopen**, or **Delete** to update/delete records through callback queries.
5. Send `/stats` or tap **Stats** to run an aggregate query.
6. In the private bot chat, tap the **My notes** menu button or send `/app` to open the web interface.

## Mini App

`webapp/` contains a dependency-free mobile interface hosted at
`https://app<app_id>.tgcloud.ai/`. It follows Telegram's theme and supports adding,
completing, reopening, deleting, and refreshing notes. Outside Telegram it displays
instructions to open the bot; it does not expose notes or use a development login.

The browser calls `Telegram.WebApp.Serverless.call('notes', input, callback)`.
Telegram verifies the Mini App init data before invoking `tgcloud/endpoints/notes.js`.
The endpoint uses only `ctx.initData.user.id` for ownership, ignoring client-provided
user/chat IDs. It shares notes with that user's **private bot chat**; group notes
are intentionally not included. Add requests carry stable IDs so retrying after a
timeout does not create duplicates. Both bot and app display the newest ten notes.

No frontend build tooling is required: `just build` syntax-checks browser and
server code, and `just deploy` publishes the static files alongside the endpoints.

Commands addressed to this bot (`/notes@YourBot`) work in groups. Notes belong to the sender within the current chat. Everyone in a group can see the bot's replies, but buttons cannot read or mutate another user's records. A button generates a fresh reply, so old panels remain visible; **Refresh** reads current data.

## Code map

| File | Example |
| --- | --- |
| `tgcloud/handlers/message.js` | Command routing and validation |
| `tgcloud/handlers/callback_query.js` | Callback acknowledgement and button actions |
| `tgcloud/schema.js` | Table, defaults, primary key, and ownership index |
| `tgcloud/lib/notes.js` | Parameterized SQL create/read/update/delete and counts |
| `tgcloud/lib/views.js` | Text and inline keyboards |
| `tgcloud/endpoints/notes.js` | Authenticated Mini App CRUD endpoint |
| `webapp/` | Mobile HTML/CSS/JS interface, hosted by Telegram |
| `scripts/setup.js` | Bot API token verification and command registration |
| `docs/tgcloud-sdk.md` | Official SDK reference generated by the CLI |

The database persists between invocations. Stable `chat_id:message_id` note IDs deduplicate message retries. Complete/reopen set explicit states rather than toggling; delete is safe to repeat. Replies themselves are not deduplicated, and Telegram message delivery is not atomic with database writes. This example retains notes until deleted; it lists only the newest ten, with no pagination.

## Verification and debugging

`npm test` executes the actual handlers and SQL against in-memory SQLite, replacing the SDK boundary and recording outgoing API calls. It covers CRUD, ownership, duplicate delivery, invalid callbacks, SQL-like input, and message limits. The schema DSL is adapted locally for tests; these tests do not verify Telegram's hosted runtime or migrations.

After configuring the CLI token, run a handler on Telegram with your local code:

```sh
npm run cloud -- run handlers/message '{chat:{id:YOUR_CHAT_ID},from:{id:YOUR_USER_ID},message_id:123,text:"/notes"}'
npm run cloud -- webhook
```

Replace the IDs with real numeric IDs. `cloud run` uses the live database and sends real messages; it is not a dry run. Use `/notes` for a read-only database check. No hosted verification or deployment is possible using only `BOT_TOKEN`.
