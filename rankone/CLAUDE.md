# Rankone

JSON API client for the Rank One (ROC) face recognition server.

## Setup

- Python 3.13+, managed with `uv`
- `just` for task running (loads `.env` automatically)
- `RANKONE` env var must point to the roc-serve URL

## Key details

- The server speaks protobuf but accepts JSON when `Content-Type: application/json` is set
- Proto field names map to JSON camelCase (e.g. `represent`, `compareTemplates`, `versionString`)
- The proto field for face representation is `represent`, NOT `representFace` (the docs' JSON example is misleading)
- Image bytes are base64-encoded strings in JSON (`base64.b64encode(image).decode()`)
- Algorithm options use string arrays (`algorithmOptions`) since bitmasking is not supported in JSON

## Test images

- `faces/a1.jpg`, `faces/a2.jpg` — same person (expect high similarity)
- `faces/b.jpeg` — different person
