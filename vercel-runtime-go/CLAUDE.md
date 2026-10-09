# vercel-runtime-go

Small Go HTTP server that renders its environment variables as an htmx-filterable
table. Deployed on Vercel as project `runtime-go` (team `me-default`),
production URL https://runtime-go.vercel.app.

## Layout

- `main.go` – the real entrypoint, both locally and on Vercel. Listens on `PORT`
  (falls back to 8000 locally).
- `internal/web/` – handler package. Templates and static files live here and
  are embedded into the binary with `go:embed`.
- `internal/web/static/htmx.min.js` – vendored htmx 2.0.8. Update by replacing
  the file; do not pull it from a CDN.
- `vercel.json` – framework preset, Fluid compute, region.
- `.vercelignore` – keeps local-only files (`exe`, `tmp`, `Makefile`) out of the
  upload. `main.go` must NOT be listed here or Vercel finds no entrypoint.

## Vercel setup

- **Zero-config Go backend**, not the `api/` function convention. Vercel's Go
  Framework Preset detects root `go.mod` + `main.go` and runs the program as a
  long-lived server. `vercel.json` sets `"framework": "go"`.
- **Never create an `api/` directory.** Vercel would build every `.go` file in
  it as a separate Lambda-style function alongside the server.
- **Fluid compute** is enabled per deployment with `"fluid": true` in
  `vercel.json`. The project predates Vercel's Fluid-by-default date, so the
  project-level toggle is off and the config entry is what makes it Fluid.
  Verify at runtime: `VERCEL_FLUID=1` is present and the `AWS_LAMBDA_*`
  variables are absent. Many concurrent requests share one process, so the
  handler must stay safe for concurrent use.
- **Region** is London, `"regions": ["lhr1"]`. Hobby plan allows one region.
- **Go version** comes from the `go` directive in `go.mod`. Vercel downloads
  and caches that exact toolchain, so use a full patch version (`go 1.27.1`),
  not a bare minor.
- **Deploys are CLI-only.** The project is not connected to the GitHub repo
  (`begoon/tmpz`); pushing does nothing. `make deploy` runs
  `vercel deploy --prod` and uploads the working tree as-is, committed or not.
  Vercel runs its own `go build`; no local build is needed first.
- **Version badge** reads `VERCEL_GIT_COMMIT_SHA`, which the CLI deploy fills
  from the local repo, with a fallback to Go's VCS build stamp locally.

## Static assets and caching

- Static files are served with a one-year `immutable` cache header. The
  `static` template func appends a content hash (`?v=...`) to asset URLs so a
  changed file gets a fresh URL. Always link assets through that func, never
  with a bare `/static/...` path, or the CDN serves the stale version.

## Environment page

- The index page prints every environment variable. Values of known secrets
  (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`,
  `VERCEL_DEPLOYMENT_KEY`, `VERCEL_ENV_ENC_KEY`) are redacted to
  `xxxx...xxxx` via the `secretEnv` set in `internal/web/index.go`. When a new
  deployment mode exposes new secret-looking variables, add them there.

## Local development

- `make dev` runs `air`, which rebuilds on `.go`, `.html`, `.css` and `.js`
  changes (CSS/JS need a rebuild because they are embedded).
- `make build` produces `./exe`. No Tailwind or other asset pipeline; the
  stylesheet is plain hand-written CSS.
