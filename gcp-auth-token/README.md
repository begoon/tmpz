# GCP authenrication token

export GOOGLE_ACCESS_TOKEN=$(gcloud auth print-access-token)

`encrypted_key.txt` contains an encrypted value in base64.

`PROFILE_META_KEY` contains a KMS key location, for example:

```env
PROFILE_META_KEY=projects/<PROJECT>/locations/global/keyRings/<KEY_RING>/cryptoKeys/<KEY_NAME>
```
