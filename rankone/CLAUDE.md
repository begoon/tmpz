# Rankone

JSON API client for the Rank One (ROC) face recognition server.

## Setup

- Python 3.13+, managed with `uv`
- `just` for task running (loads `.env` automatically)
- `RANKONE` env var must point to the roc-serve URL

## Usage

- `just version` — print server version
- `just represent <image>` — detect face, output `result.jpg` with bounding box and keypoints
- `just compare <image1> <image2>` — compare two faces, output `result.jpg` side-by-side with similarity score

## Key details

- The server speaks protobuf but accepts JSON when `Content-Type: application/json` is set
- Proto field names map to JSON camelCase (e.g. `represent`, `compareTemplates`, `versionString`)
- The proto field for face representation is `represent`, NOT `representFace` (the docs' JSON example is misleading; changed to `representFace` in v3.5.0+)
- Image bytes are base64-encoded strings in JSON (`base64.b64encode(image).decode()`)
- Algorithm options use string arrays (`algorithmOptions`) since bitmasking is not supported in JSON
- RPC calls retry up to 3 times with exponential backoff on 5xx/transport errors (via tenacity); 4xx errors raise immediately

## Test images

- `faces/a1.jpg`, `faces/a2.jpg` — same person (expect high similarity ~0.99)
- `faces/b.jpeg` — different person (expect similarity ~0.0)
