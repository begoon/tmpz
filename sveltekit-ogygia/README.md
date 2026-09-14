# SvelteKit × ogygia × Bun — partial hydration demo

An example SvelteKit app, run with [Bun](https://bun.sh), that uses
[ogygia](https://github.com/PuruVJ/ogygia) for **island (partial) hydration**: the page shell is
plain server-rendered HTML with no SvelteKit client runtime, and only the components you mark get
JavaScript in the browser — each on its own schedule.

## Run it

```bash
bun install
bun run dev        # Vite dev server under Bun → http://localhost:5173
bun run build      # production build (adapter-node) into ./build
bun run start      # bun ./build/index.js
bun run check      # svelte-check
```

## What the home page demonstrates

| Card | Import attribute | Behaviour |
| --- | --- | --- |
| Static component | *(none)* | Server HTML only. Its button is deliberately dead. |
| Counter | `with { wake: 'load' }` | Hydrates immediately, with `modulepreload` hints. |
| Clock | `with { wake: 'idle' }` | Hydrates in `requestIdleCallback`. |
| Streamed page data | `with { wake: 'load' }` | Reads `page.data` inside an island. A promise from `load` streams in after first paint. |
| Accordion | `with { wake: 'interaction' }` | No JS until the first click, which is then replayed. |
| Media-query island | `with { wake: '(min-width: 900px)' }` | Hydrates only on wide viewports. |
| Cart badge + Add to cart | `wake: 'load'` / `wake: 'visible'` | Two islands share one live `Cart` instance via a `wire` codec. |
| Server island | `with { render: 'deferred', wake: 'load' }` | Not rendered during the page request. A fallback ships, the HTML is fetched from a signed endpoint, and no client JS is involved. |
| Chart | `with { preset: 'chart' }` | A named preset (`wake: 'visible'` with a 300px margin) defined in `vite.config.ts`. |

Islands that have hydrated get a green outline (CSS on `ogygia-region[data-hydrated]`), and every
island shows a badge that flips from “server HTML only” to “hydrated at …” when its JS runs.

## The three pieces of setup

1. **`src/routes/+layout.ts`** — `export const csr = false;` turns off Kit's client runtime.
2. **`vite.config.ts`** — `plugins: [ogygia({ … }), sveltekit()]`. ogygia must come first.
3. **`src/hooks.server.ts`** — `export const handle = ogygiaHandle();` serves the endpoint that
   server islands fetch their HTML from.

`svelte.config.js` additionally enables `compilerOptions.experimental.async` so a server island can
`await` at the top of its script, and adds `ogygia.preprocess()` for the `ogygiaFallback` snippet.

## Where to look

- `src/routes/+page.svelte` — every island import lives here, one per strategy.
- `src/lib/*.svelte` — the island components. They are ordinary Svelte 5 components; nothing in
  them knows about ogygia.
- `src/lib/cart.svelte.ts` — the `static wire = import.meta.og.wire({ encode, decode })` codec that
  lets one class instance be shared across islands.
- `src/lib/ServerTime.svelte` — the server island. It reports whether it was rendered by Bun or Node.
- `src/routes/how-it-works/+page.svelte` — a zero-JS page explaining the mechanism.

## Environment

`OGYGIA_SECRET` (see `.env.example`) signs server-island URLs. It is optional for a single process;
set it when running several instances so they accept each other's URLs.

## Versions used

SvelteKit 2.70, Svelte 5.57, Vite 8.3, ogygia 0.7, Bun 1.4.
