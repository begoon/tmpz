# Rankone Web

SvelteKit app for visual face and fingerprint biometric operations using Rankone servers.

## Stack

- **SvelteKit** (Svelte 5 with runes mode) + TypeScript
- **Bun** as package manager and runtime
- `bun install`, `bun run dev`, `bun run build`

## Project Structure

- `src/lib/rankone.ts` — server-side Rankone RPC client (face 330, fingerprint 250)
- `src/routes/+page.svelte` — main UI (placeholders, gallery, drag-drop, canvas detections)
- `src/routes/+page.server.ts` — page load (fetches server versions)
- `src/routes/api/represent/+server.ts` — face represent proxy
- `src/routes/api/represent-fingerprint/+server.ts` — fingerprint represent proxy
- `src/routes/api/compare/+server.ts` — compare templates proxy
- `static/i/` — sample face and fingerprint images

## Environment

Uses SvelteKit's `$env/static/private` for env vars (not `process.env`).

Required in `.env`:

- `RANKONE_330` — Face server URL (ROC v3.3.0)
- `RANKONE_250` — Fingerprint server URL (ROC v2.5.0)

## Rankone API

- **represent** (face, 330): `{ represent: { image, algorithmOptions, ... } }` → templates with detection + keypoints
- **representFingerprint** (fingerprint, 250): `{ representFingerprint: { image, fingerOptions, ... } }` → templates with detection (no keypoints)
- **compareTemplates**: `{ compareTemplates: { a, b } }` → `{ similarity: float }`
- **versionString**: `{ versionString: {} }` → `{ versionString: { version: "3.3.0" } }`
- Detection coordinates are center-based: `x, y` = center, `width, height` = box size
- Face keypoints: leftEye, rightEye, nose, rightMouthCorner, leftMouthCorner, chin

## UI Behavior

- Drop image onto placeholder → auto-detect type (face/fingerprint) via both APIs, draw bbox + confidence
- Two same-type images → auto-compare and show similarity
- Double-click placeholder to clear it
- Similarity resets when a slot is cleared or a new image is dropped

## Drawing Conventions

- Bounding box: lightskyblue, 2px stroke
- Face keypoints: white X markers (crosshairs)
- Confidence shown as text below placeholder, not on canvas
