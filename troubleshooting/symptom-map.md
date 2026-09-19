# OAuth/OIDC Troubleshooting Symptom Map

Use this only as a starting point. Always confirm the failed step from the actual request, response, token, and Okta System Log.

| Symptom | First areas to investigate |
|---|---|
| Redirect URI error | Requested callback URI vs registered sign-in redirect URI |
| `invalid_client` | Client ID, configured token endpoint auth method, secret/key/assertion |
| `invalid_grant` | Authorization code expiry/reuse, redirect URI equality, PKCE verifier, refresh-token state |
| `invalid_scope` | Requested scope, authorization server, access policy/rule, allowed scope |
| No refresh token returned | `offline_access`, Refresh Token grant enabled, authorization-server policy |
| API returns 401 | Token present? correct token type? signature, issuer, audience, expiry, JWKS |
| API returns 403 | Token accepted but required scope/claim/permission missing |
| Unknown `kid` | Wrong issuer/JWKS, stale key cache, signing-key rotation |
| Audience mismatch | Wrong authorization server, wrong configured audience, wrong token sent to API |
| Unexpected MFA | Global Session Policy, App Sign-In/Authentication Policy, existing session state |
| Expected scope missing | Was it requested? Did the matching authorization-server rule permit it? |
| Login works but profile claim is missing | Requested OIDC scopes, claim configuration, ID token vs `/userinfo` expectation |
| App logout signs user straight back in | Local application session ended but Okta browser session remains |
| Postman works but SPA fails | CORS, Trusted Origins where applicable, browser cookies, callback handling, PKCE state |
| Works in dev but fails in prod | Issuer, client ID, redirect URI, secret/key, policy, assignment, audience, environment config |
| Token is revoked but API still accepts it | API is probably doing local JWT validation and not checking live revocation state |
| Okta API token obtained but operation denied | OAuth scope may be present while admin role/resource permission is insufficient |

## Investigation order

Ask:

> What is the last step I can prove succeeded?

Then follow the transaction:

```text
1. App builds request
2. Browser reaches /authorize
3. User authentication / policy evaluation
4. Callback / authorization response
5. Authorization code returned
6. Client calls /token
7. Tokens issued
8. Client validates OIDC response / ID token
9. Client calls API with access token
10. API validates access token
11. API authorizes the operation
```

## Evidence rule

When available, use all three:

1. Browser Network tab, curl, or Postman
2. Token inspection
3. Okta System Log

A setting change is not the diagnosis. The diagnosis is the failed step, the evidence showing why it failed, and proof that the corrected configuration changed that behavior.
