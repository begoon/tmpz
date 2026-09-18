# kmp-server

Demo REST server written in Kotlin (JVM) with Ktor.

| Endpoint  | Response                |
|-----------|-------------------------|
| `GET /`   | `ok` (text/plain)       |
| `GET /health` | `{"status":"UP"}` (application/json) |

## Commands

```sh
just build      # check formatting, compile and assemble
just serve      # start on http://localhost:8080 (PORT overrides)
just test       # run endpoint tests
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
