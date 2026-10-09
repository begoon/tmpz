# vercel-runtime-go

Go HTTP server on Vercel serving a vendored GitHub profile README at `/` and an
htmx-filterable table of its environment variables at `/env`.

Production: https://demin.page (also https://runtime-go.vercel.app)

- `make dev` – run locally with air on http://localhost:8000
- `make deploy` – deploy to production (CLI upload, no git integration)
- `make vendor-readme` – refresh the vendored profile README from GitHub

See `CLAUDE.md` for the Vercel setup details.

## demin.page DNS backup

Snapshot of the Squarespace DNS settings for `demin.page` taken on
2026-10-09, before the apex A records were pointed at Vercel. Keep this in case
the domain needs to go back to GitHub Pages.

Registrar: Squarespace (ex Google Domains). The zone itself was hosted on the
legacy Google Cloud DNS nameservers listed below.

### Nameservers

| Nameserver                      |
| ------------------------------- |
| `ns-cloud-d1.googledomains.com` |
| `ns-cloud-d2.googledomains.com` |
| `ns-cloud-d3.googledomains.com` |
| `ns-cloud-d4.googledomains.com` |

### Preset: Squarespace Email Forwarding (Mailgun)

| Type | Name | Priority | TTL   | Data                              |
| ---- | ---- | -------- | ----- | --------------------------------- |
| MX   | `@`  | 10       | 4 hrs | `mxa.mailgun.org`                 |
| MX   | `@`  | 10       | 4 hrs | `mxb.mailgun.org`                 |
| TXT  | `@`  |          | 4 hrs | `v=spf1 include:mailgun.org ~all` |

### Preset: Squarespace Domain Connect

| Type  | Name             | TTL  | Data                                       |
| ----- | ---------------- | ---- | ------------------------------------------ |
| CNAME | `_domainconnect` | 1 hr | `_domainconnect.domains.squarespace.com`   |

### Custom records

| Type  | Name              | TTL   | Data                                     |
| ----- | ----------------- | ----- | ---------------------------------------- |
| A     | `@`               | 4 hrs | `185.199.108.153` (GitHub Pages)         |
| A     | `@`               | 4 hrs | `185.199.109.153` (GitHub Pages)         |
| A     | `@`               | 4 hrs | `185.199.110.153` (GitHub Pages)         |
| A     | `@`               | 4 hrs | `185.199.111.153` (GitHub Pages)         |
| CNAME | `kd4pzovdt4si`    | 4 hrs | `gv-z5tmbpsxhb2oi6.dv.googlehosted.com`  |
| TXT   | `krs._domainkey`  | 4 hrs | DKIM key, full value below               |

The `kd4pzovdt4si` CNAME is a Google site-verification record. The
`krs._domainkey` TXT is the Mailgun DKIM key. Its full value (the Squarespace
UI truncates it) as published in DNS:

```
k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC2lLyzQjM+EiIWeZIC4LQzbTDLxgipYcOmO1AMMmB76buWi7fLSjAxBBZ/TR39GP0oeIEnPwELlvW1NvBHoI7HVcD6NQCMEfH7ip/bUNJf2+l0DceNhYSxNfyMXaeK7+5SrVOJKEMe8AKnu4MrIPsdtb/lYWJ9KVrs+5lAGFxP8QIDAQAB
```

### Current state (after the move to Vercel)

Only the apex A records changed. Mail, DKIM and verification records are
untouched. The apex now resolves to Vercel's A records:

| Type | Name | Data            |
| ---- | ---- | --------------- |
| A    | `@`  | `216.198.79.1`  |
| A    | `@`  | `64.29.17.1`    |

### Going back to GitHub Pages

1. In the DNS provider, delete the two Vercel A records on `@`.
2. Re-add the four GitHub Pages A records from the custom records table above.
3. Remove `demin.page` from the Vercel project
   (`vercel domains rm demin.page`) so Vercel stops trying to renew its
   certificate.
4. Re-enable the custom domain in the GitHub Pages repository settings and
   wait for GitHub to issue its certificate.
