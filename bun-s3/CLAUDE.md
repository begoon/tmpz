# CLAUDE.md

## Project overview

Bun-based examples for accessing S3-compatible object storage across providers (GCS, OCI). Uses Bun's built-in `Bun.S3Client` for file operations and manual AWS Signature V4 signing for bucket listing (since Bun's client doesn't support list).

## Running

```
bun <filename>.ts
```

All credentials are in `.env` (loaded automatically by Bun). Do not commit `.env`.

## Key files

- `bucket-s3.ts` -- reads a file from GCS
- `bucket-gcs.ts` -- lists + reads from GCS
- `bucket-oci.ts` -- lists + reads from OCI Object Storage
- `.env` -- S3-compatible credentials for each provider (GCS_*, OCI_*, S3_*)

## Conventions

- Each `bucket-*.ts` file is self-contained -- no shared modules
- Listing uses manual SigV4 signing; file read/write uses `Bun.S3Client`
- Endpoint format: GCS uses `https://storage.googleapis.com`, OCI uses `https://<namespace>.compat.objectstorage.<region>.oraclecloud.com`
