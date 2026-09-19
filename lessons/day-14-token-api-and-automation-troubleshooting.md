## Day 14 — Token, API, and automation troubleshooting

### Case 1 — `invalid_client`

Work the client-authentication layer:

```text
client ID
configured auth method
secret/key
kid
assertion aud
assertion exp
endpoint
```

Do not waste time debugging user MFA for a service-client `invalid_client` error.

### Case 2 — `invalid_grant`

First identify the grant you are using.

For Authorization Code:

```text
code expired/reused?
redirect URI mismatch?
PKCE verifier wrong?
wrong client/transaction?
```

For refresh:

```text
refresh token revoked/expired?
rotation/reuse issue?
wrong client?
```

The same error name can have different causes because different grants use different credentials.

### Case 3 — `invalid_scope`

Ask:

```text
Which authorization server?
Does that scope exist there?
Was the scope requested in the right place?
Does the client/policy permit it?
For Okta API service app, is the Okta API scope granted to the app?
```

### Case 4 — API 401

Use a validation checklist:

```text
Bearer token actually present?
Correct token type?
Correct issuer?
Correct audience?
Signature valid?
Token expired/not-before valid?
JWKS current?
```

### Case 5 — API 403

If token validation succeeded, move to permission:

```text
required scope present?
required claim/role present?
API's own authorization logic correct?
```

### Case 6 — unknown `kid`

Likely branches:

```text
wrong issuer / wrong JWKS
key rotation and stale cache
hardcoded key
malformed token header
```

Do not “fix” key rotation by permanently disabling signature validation.

### Case 7 — Dev works, prod fails

Compare environment by environment:

```text
issuer
authorization server ID
client ID
redirect URI
logout URI
secret/key
scope existence
access policy
assignment
audience
custom domain
CORS/Trusted Origin
```

This is why environment configuration belongs to engineering, not only deployment teams.

### Case 8 — Okta API token obtained, operation still denied

Separate:

```text
OAuth scope in token
vs
admin role/resource authorization
```

If scope is present but the service app is not authorized for that resource/action, rebuilding the JWT assertion does not fix the permission layer.

### Final troubleshooting drill

Have someone give you ten failures without telling you the category. For each, your first response should not be a fix. It should be:

> Show me the request/response at the failing step and the relevant System Log event.

Then reason from evidence.

---
