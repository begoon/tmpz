# zig-webview

A native macOS desktop app built with [zero-native](https://zero-native.dev): Zig backend + system WebView (WebKit) + Svelte frontend. No Electron, no bundled Chromium — the release binary is ~340 KB and links only stock macOS frameworks.

The app demonstrates the JS↔Zig bridge with two endpoints:

- `system.info` — returns `uname` fields and CPU count from Zig
- `counter.{get,increment,reset}` — `i32` state lives in the Zig `App` struct, mutated via bridge calls

## Layout

```
.
├── Justfile               # dev / build / run-app / clean recipes
├── trial/                 # the app
│   ├── app.zon            # manifest: bundle id, window, web engine, security
│   ├── build.zig          # build graph
│   ├── src/main.zig       # bridge handlers, dispatcher, app entry
│   ├── src/runner.zig     # platform-specific runtime wiring
│   ├── assets/icon.icns
│   └── frontend/          # Svelte 5 + Vite
│       └── src/App.svelte # UI that calls window.zero.invoke(...)
└── .cli-install/          # locally-bootstrapped zero-native CLI (gitignored)
```

## Prerequisites

- macOS (Apple Silicon or Intel)
- Zig 0.16.0+
- Node.js / npm
- [just](https://github.com/casey/just): `brew install just`

## First-time setup

The `zero-native` CLI is bootstrapped locally rather than installed globally:

```sh
mkdir -p .cli-install && cd .cli-install
printf '{"name":"cli-install","version":"1.0.0","private":true}\n' > package.json
npm install zero-native
```

The Justfile prepends `.cli-install/node_modules/.bin` to `PATH`, so `zig build` finds the CLI without further configuration.

## Develop

```sh
just dev
```

Runs `zig build dev` from `trial/`: Vite dev server with HMR on `http://127.0.0.1:5173`, native shell points at it via `ZERO_NATIVE_FRONTEND_URL`. Edit `frontend/src/App.svelte` and changes hot-reload in the native window.

## Build a standalone .app

```sh
just build
```

Produces `trial/zig-out/package/trial-0.1.0-macos-ReleaseSmall.app` (~408 KB total, ~340 KB binary). The recipe also runs `chmod +x` on the inner binary — zero-native 0.1.9 packages it without the execute bit, which makes Finder reject it ("can't be opened"). Drop this step once [vercel-labs/zero-native](https://github.com/vercel-labs/zero-native) ships a fix.

```sh
just run-app    # open the most recently built bundle
just clean      # rm -rf zig-out .zig-cache frontend/dist frontend/node_modules
```

The bundle is unsigned. On first launch macOS Gatekeeper blocks it — right-click → Open, or:

```sh
xattr -dr com.apple.quarantine trial/zig-out/package/trial-*.app
```

## How the bridge works

JS side — every WebKit window gets `window.zero` injected by the zero-native AppKit host:

```js
const { value } = await window.zero.invoke("counter.increment");
```

Zig side — a handler function with signature `fn(ctx, invocation, output) ![]const u8` writes a JSON result, registered on a `BridgeDispatcher`:

```zig
const dispatcher = zero_native.BridgeDispatcher{
    .policy = .{ .enabled = true, .commands = &command_policies },
    .registry = .{ .handlers = &handlers },
};
```

Each command is allowlisted to specific origins (`zero://app`, `zero://inline`, `http://127.0.0.1:5173` for dev) — calls from anywhere else return `permission_denied`.

## Runtime artifacts

- Logs: `~/Library/Logs/dev.zero_native.trial/zero-native.jsonl`
- Window state: `~/Library/Application Support/dev.zero_native.trial/State/windows.zon`

Default trace level is `events`. Rebuild with `-Dtrace=all` (or just `bridge`) to log every bridge invocation.

## Switching to Chromium/CEF

System WebView keeps the binary tiny but renders with whatever WebKit version ships with macOS. For consistent rendering across platforms, bundle CEF:

```sh
zero-native cef install
zig build run -Dweb-engine=chromium
```

The bundle balloons to ~120 MB. Set `web_engine = "chromium"` in `app.zon` to make this the default.
