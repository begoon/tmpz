# Rankone

JSON API clients for Rank One (ROC) biometric servers (face and fingerprint).

## Setup

- Python 3.13+, managed with `uv`
- `just` for task running (loads `.env` automatically)
- `RANKONE_330` env var — ROC v3.3.0 server URL (faces)
- `RANKONE_250` env var — ROC v2.5.0 server URL (fingerprints)

## Usage — faces (`rankone_face.py`)

- `just version-face` — print server version
- `just represent-face <image>` — detect face, output `result.jpg` with bounding box and keypoints
- `just compare-face-match` / `just compare-face-mismatch` — compare two faces, output `result.jpg` side-by-side with similarity score

## Usage — fingerprints (`rankone_fingerprints.py`)

- `just version-fingerprints` — print server version
- `just represent-fingerprints <image>` — detect fingerprint, output `result.jpg` with bounding box
- `just compare-fingerprints-match` / `just compare-fingerprints-mismatch` — compare two fingerprints, output `result.jpg` side-by-side with similarity score

## Code structure

- `rankone.py` — shared RPC client (`rpc`, `version_string`, `compare_templates`)
- `draw.py` — shared drawing (`draw_template`, `draw_compare`), takes `draw_detection`/`scale_detection` callbacks
- `rankone_face.py` — face-specific represent + detection drawing (bounding box + keypoints)
- `rankone_fingerprints.py` — fingerprint-specific represent + detection drawing (bounding box only)

## Key details

- The server speaks protobuf but accepts JSON when `Content-Type: application/json` is set
- Proto field names map to JSON camelCase (e.g. `represent`, `compareTemplates`, `versionString`)
- The proto field for face representation is `represent`, NOT `representFace` (the docs' JSON example is misleading; changed to `representFace` in v3.5.0+)
- The proto field for fingerprint representation is `representFingerprint`
- Image bytes are base64-encoded strings in JSON (`base64.b64encode(image).decode()`)
- Face algorithm options use string arrays (`algorithmOptions`) since bitmasking is not supported in JSON
- Fingerprint options use `fingerOptions` array; use `ROC_UNKNOWN_FINGER` for single-finger images (not `ROC_INDEX_FINGER`, which produces non-comparable templates)
- RPC calls retry up to 3 times with exponential backoff on 5xx/transport errors (via tenacity); 4xx errors raise immediately

## Test images

- `i/faces/a1.jpg`, `i/faces/a2.jpg` — same person (expect high similarity ~0.99)
- `i/faces/b.jpg` — different person (expect similarity ~0.0)
- `i/fingerprints/a1.png`, `i/fingerprints/a2.png` — same finger (expect similarity ~1.0)
