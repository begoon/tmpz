# Trivia Worker

A small Cloudflare Worker with a KV-backed page-load counter and a Flagship-controlled Reset button. Uses plain HTML with no frontend framework.

Live: https://trivia.acula.workers.dev/

## Routes

| Route | Behavior |
| --- | --- |
| `GET /` | Increments the counter and renders `OK` followed by its value. |
| `HEAD /` | Returns page headers without incrementing the counter. |
| `GET /health` | Returns `{"status":"ok"}`. |
| `POST /reset` | Deletes the counter and redirects to `/` when the feature flag is on; otherwise returns 404. |

The Reset button submits a form. The redirected page load increments the cleared counter to `1`. Other paths return 404.

## Development

Install Node.js and npm, then run:

```sh
npm ci
npm run dev
```

Wrangler serves the app at `http://localhost:8787` using local storage. Local KV data is separate from production and persists under the ignored `.wrangler/` directory.

To enable Reset locally, create a local flag:

```sh
npx wrangler flagship flags create 61368047-9dc1-466e-9781-ab012fd7a247 reset-button --local --type boolean --variation on=true --variation off=false --default off --rule 'serve=on'
```

If that local flag already exists, use `flags update` with `--local --enable` instead. Without a configured flag, the code defaults to hiding and disabling Reset.

## Cloudflare resources

Bindings in `wrangler.jsonc` connect the Worker to these resources:

| Binding | Resource | Purpose |
| --- | --- | --- |
| `COUNTER` | KV namespace `COUNTER` | Stores the count under the key `page-loads`. |
| `FLAGS` | Flagship app `trivia` | Contains the boolean flag `reset-button`. |

The Worker and Flagship app are separate resources. Their shared name does not connect them; the binding's app ID does. Resource IDs in the configuration belong to the current Cloudflare account. To deploy to another account, create equivalent resources and replace those IDs.

## Reset feature flag

In the Cloudflare dashboard, open **Compute → Flagship → trivia → reset-button**.

- Enabled: an unconditional rule serves the `on` variation (`true`).
- Disabled: the default `off` variation (`false`) hides the button and blocks the reset endpoint.

Changes can take up to 30 seconds to propagate. Refresh the page to see the result; no deployment is needed. See [Flagship propagation](https://developers.cloudflare.com/flagship/concepts/#flag-propagation).

To change the production flag from the CLI:

```sh
npx wrangler flagship flags update 61368047-9dc1-466e-9781-ab012fd7a247 reset-button --disable --remote
npx wrangler flagship flags update 61368047-9dc1-466e-9781-ab012fd7a247 reset-button --enable --remote
```

## Deploy

Authenticate with the account that owns the configured resources, then deploy:

```sh
npx wrangler login
npm run deploy
```

To validate the bundle without deploying:

```sh
npx wrangler deploy --dry-run
```

## Counter limitations

The counter uses a KV read followed by a write. KV is eventually consistent and does not provide atomic increments, so concurrent or geographically distributed requests may lose increments or observe stale counts. This is a demonstration counter, not an exact analytics total.

Each page load uses one KV read and one write. Workers Free currently includes 1,000 KV writes per day, and a single key is limited to one write per second. Storage failures return HTTP 503. See [KV pricing](https://developers.cloudflare.com/kv/platform/pricing/) and [KV limits](https://developers.cloudflare.com/kv/platform/limits/).

Reset is public when enabled. The endpoint checks browser request origins, but the feature flag is not authentication.
