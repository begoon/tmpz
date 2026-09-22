# kmp-server

Demo REST and websocket server written in Kotlin (JVM) with Ktor.

| Endpoint  | Response                |
|-----------|-------------------------|
| `GET /`   | dashboard page (text/html) |
| `GET /stats` | HTML fragment with ping count and RSS, used by the dashboard |
| `GET /assets/htmx/htmx.min.js` | vendored htmx script |
| `GET /health` | `{"status":"UP"}` (application/json) |
| `GET /swagger` | Swagger UI with endpoint documentation and HTTP try-it-out |
| `WS /ws/{id}` | one `Response` per `Request` (binary protobuf frames) |

## Dashboard

Open `/swagger` for API documentation, backed by `src/main/resources/openapi/documentation.json`.
HTTP endpoints can be called from Swagger UI. WebSocket protocols are documented there;
use the dashboard or `just ping` to send WebSocket messages.

`GET /` is a small [htmx](https://htmx.org) page showing pings received since startup, the number of records in `kmp.pings`, and
the server's resident memory. The `#stats` block is loaded from `GET /stats` on page load and
every 5 seconds via `hx-trigger="load, every 5s"`; a Refresh button fetches it on demand.
Only the fragment is swapped, never the whole page.

The **Send a ping** form uses the [htmx 4 WebSocket extension](https://four.htmx.org/extensions/hx-ws)
to send JSON form values to `/ping/send`. The server saves each ping with client ID `browser`
through the same handler and counter as protobuf pings, then returns HTML showing the pong
number and refreshing the stats. Connection and save failures are shown on the page.
The extension is vendored alongside htmx; `just htmx` refreshes both scripts.

htmx 4 is served by the application itself from `src/main/resources/assets/htmx/`. The file is
committed; `just htmx` re-downloads the version pinned in `gradle/libs.versions.toml` from
the jsDelivr CDN.

## Websocket

`/ws/{id}` speaks protobuf, defined in `proto/protocol.proto`. Each binary frame from
the client is a `Request` and is answered with one `Response`; both are `oneof`
envelopes, since bare protobuf messages are not self-describing.

| Request | Response | Behaviour |
|---------|----------|-----------|
| `Ping { message: string }` | `Pong { n: int32 }` | saves to MongoDB and logs the message; `n` counts received pings since this application started, across all connections |
| `QueryStatus {}` | `Status { memory: int64, state: string }` | `memory` is the resident set size of the server process in bytes, `state` is `ok` |

A text frame, a frame that is not a valid `Request`, or a `Request` with no body closes
the connection with close code 1003.

Kotlin and Java sources for the messages are generated into `src/main/generated/`
and committed, so building needs no protoc. After editing the `.proto`, run:

```sh
just protobuf   # regenerates src/main/generated with bin/protoc
```

`bin/protoc` downloads the protoc release pinned in `gradle/libs.versions.toml` into
`.tools/` on first use; the pinned version matches the protobuf runtime dependency,
which the generated code requires.

## Commands

Set `MONGODB_URI` in `.env` in the working directory (loaded automatically by `just serve`),
or export it as an environment variable. The environment takes precedence. For example:

```dotenv
MONGODB_URI=mongodb://localhost:27017
```

Each protobuf `Ping` is inserted into database `kmp`, collection `pings`, using the
[MongoDB Kotlin coroutine driver](https://www.mongodb.com/docs/drivers/kotlin/coroutine/current/).
Documents have a generated `_id`, `clientId` (the WebSocket path ID), `message`, and
`receivedAt` (a BSON UTC date). The server waits for an acknowledged insert before sending
the pong. If saving fails, the connection closes with code 1011 instead of
acknowledging the ping. Status requests and invalid frames are not saved. The in-memory counter increments for each valid ping (even if saving fails) and resets on restart.
The separate MongoDB record count is read on every stats request and browser pong update,
so it includes records from previous runs and other server instances. If counting fails,
the dashboard shows `Unavailable` while pongs continue to use the in-memory counter.
New documents do not store `n`; any `n` fields in older documents are ignored.

The server requires `MONGODB_URI` at startup, shares one MongoDB client, and closes it on
shutdown. Endpoint tests inject an in-memory substitute and never access your database.
To inspect saved pings in `mongosh`:

```javascript
db.getSiblingDB("kmp").pings.find().sort({ receivedAt: -1 }).limit(10)
```

```sh
just build      # check formatting, compile and assemble
just serve      # start on http://localhost:8080 (PORT overrides)
just ping       # send a WebSocket ping to the running server and print the pong
just test       # run endpoint tests
just protobuf   # regenerate protobuf sources from proto/protocol.proto
just htmx       # re-download the pinned htmx release into src/main/resources/assets/htmx
just fmt        # reformat all Kotlin with ktfmt
just fmt-check  # formatting check only
just clean      # stop Gradle daemons, remove build/, .gradle/, .kotlin/, .tools/
```

With the server running, `just ping` sends `hello` to `/ws/just-ping` on localhost
(using `PORT`, or 8080). It saves a ping in MongoDB through the normal server handler
and prints `Pong: n=...`. An optional message and full WebSocket URL can be supplied:

```sh
just ping "hello from the command line"
just ping "hello" "ws://localhost:9090/ws/my-client"
```

The command exits with an error if the request fails or no pong arrives within 10 seconds.

## Formatting

Kotlin is formatted with [ktfmt](https://github.com/facebook/ktfmt) in `kotlinlang` style.
`just build` fails on unformatted code. The version is pinned once in
`gradle/libs.versions.toml` and used by both Gradle and `bin/ktfmt`.

VS Code formats on save via the recommended extensions (`.vscode/extensions.json`):
the JetBrains Kotlin extension for language support and Custom Local Formatters,
which runs `bin/ktfmt` on the buffer. The ktfmt jar downloads into `.tools/` on first use.

Requires JDK 17+ and `just`. Gradle is provided by the wrapper.

## Docker

```sh
just docker-build          # builds the kmp-server image
just docker-run            # runs it on http://localhost:8080
just docker-run 9090       # or any other host port
```

`just docker-run` passes `.env` to the container with `--env-file`; `.env` is excluded
from the Docker build context.
