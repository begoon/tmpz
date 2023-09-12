# Generate refresh token

<https://www.youtube.com/watch?v=18qA61bpfUs>
<https://stateful.com/blog/gmail-api-node-tutorial>

- GCP "APIs and Services"
- create credentials "OAuth2 2.0 ClientIDs"

"Authorised redirect URIs" = "https://developers.google.com/oauthplayground"

- save client ID and client secret
- create an OAuth consent screen
- add a test user in there which will be used to authorise "mail.google.com" on
- publish the app

- go to https://developers.google.com/oauthplayground
- click the settings icon (top right)
- check "Use your own OAuth credentials"
- enter your client ID and client secret
- click "Close"
- in the left pane, scroll down to "Gmail API v1" (or "https://mail.google.com")
- click the checkbox
- click "Authorize APIs"
- click "Allow"
- click "Exchange authorization code for tokens"
- copy the refresh token

## CLI

```bash
bun main.js --labels
bun main.js <label>
bun main.js <label> --messages
bun main.js <label> --delete
```
