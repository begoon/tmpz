# bun-s3

Using Bun's built-in S3 client with S3-compatible object storage providers.

## S3 as a de facto standard

S3 is the de facto standard for object storage APIs. Almost every cloud provider and storage system offers an S3-compatible endpoint:

- **AWS S3** (the original)
- **Google Cloud Storage** (GCS)
- **OCI Object Storage**
- **Cloudflare R2**
- **MinIO**, **Ceph**, **Backblaze B2**, **DigitalOcean Spaces**, **Wasabi**, etc.

They all speak the same protocol -- AWS Signature V4 auth, the same REST verbs, same XML responses. You just swap the `endpoint`, `accessKeyId`, and `secretAccessKey`.

## S3 protocol essentials

There is no separate "S3 protocol spec" -- the AWS API docs *are* the spec, and every compatible provider reverse-engineered from them.

The core is a handful of operations:

| Operation      | HTTP                         |
|----------------|------------------------------|
| ListObjectsV2  | `GET /{bucket}?list-type=2`  |
| GetObject      | `GET /{bucket}/{key}`        |
| PutObject      | `PUT /{bucket}/{key}`        |
| DeleteObject   | `DELETE /{bucket}/{key}`     |
| HeadObject     | `HEAD /{bucket}/{key}`       |

...plus Signature V4 on every request.

### References

- [S3 REST API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations_Amazon_Simple_Storage_Service.html) -- the definitive list of operations, request/response formats
- [Signature V4 signing](https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html) -- the auth mechanism everyone implements

## Native APIs vs S3 compatibility

Each provider also has its own native API (GCS uses JSON REST with OAuth2, OCI uses RSA signature-based auth, Azure has Shared Key / SAS tokens). The S3-compatible endpoints are an additional layer these providers offer because S3 became the standard.

There is no meaningful speed difference between native and S3-compatible APIs -- the data transfer is the same HTTP/TLS over the same network path. Native SDKs may offer features like resumable uploads or parallel composite transfers, but S3 also supports multipart uploads.

## Notes

- Bun's S3 client handles Signature V4 signing transparently for file operations (read, write, delete, presign)
- Bun's S3 client does **not** support listing objects -- the examples use the S3 REST API directly with manual SigV4 signing for that
- S3-compatible credentials (access key + secret key) are different from native API credentials -- e.g., OCI requires generating "Customer Secret Keys" separately from its API signing keys

## Examples

- `bucket-s3.ts` -- read a file from Google Cloud Storage (GCS via S3-compatible HMAC keys)
- `bucket-gcs.ts` -- list objects and read a file from GCS
- `bucket-oci.ts` -- list objects and read a file from OCI Object Storage
