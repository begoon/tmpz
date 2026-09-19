# kmp-server

Demo REST and websocket server written in Kotlin (JVM) with Ktor.

| Endpoint  | Response                |
|-----------|-------------------------|
| `GET /`   | `ok` (text/plain)       |
| `GET /health` | `{"status":"UP"}` (application/json) |
| `WS /ws/{id}` | one `Response` per `Request` (binary protobuf frames) |

## Websocket

`/ws/{id}` speaks protobuf, defined in `proto/protocol.proto`. Each binary frame from
the client is a `Request` and is answered with one `Response`; both are `oneof`
envelopes, since bare protobuf messages are not self-describing.

| Request | Response | Behaviour |
|---------|----------|-----------|
| `Ping { message: string }` | `Pong { n: int32 }` | logs the message; `n` counts pings since the server started, across all connections and ids |
| `GetStatus {}` | `Status { memory: int64, state: string }` | `memory` is the resident set size of the server process in bytes, `state` is `ok` |

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

```sh
just build      # check formatting, compile and assemble
just serve      # start on http://localhost:8080 (PORT overrides)
just test       # run endpoint tests
just protobuf   # regenerate protobuf sources from proto/protocol.proto
just fmt        # reformat all Kotlin with ktfmt
just fmt-check  # formatting check only
just clean      # stop Gradle daemons, remove build/, .gradle/, .kotlin/, .tools/
```

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
