## Day 6 — Okta application configuration and client authentication

### Stop treating the Okta app screen as a checklist

Every field exists because it changes protocol behavior or who is allowed to use the integration.

Before creating the app, know the architecture.

### Application type

If you choose SPA for something that is really a confidential backend, or Web for browser-only JavaScript, you can end up with the wrong client-authentication assumptions.

Map the runtime first:

```text
SPA       → public client
Native    → public client
Web       → usually confidential server-side client
API Service → confidential service client
```

### Client ID

The client ID is an identifier, not a secret.

It appears openly in authorization requests. Do not waste effort “hiding” a client ID.

### Redirect URI

The redirect URI is a security boundary. Okta should return an authorization response only to a registered location.

Real mistakes:

```text
http vs https
localhost:3000 vs localhost:3001
/callback vs /login/callback
/test callback used in prod
custom domain URL mixed with org domain assumptions
```

Treat it as exact configuration, not a friendly destination label.

### Assignments / Controlled Access

If the app is restricted to assigned users/groups, assignment is part of the authorization to use the application.

But do not blindly tell every unassigned-login ticket “assign the user.” First check whether the app is configured for assigned access or everyone in the org.

System Log is valuable because it tells you why Okta denied the transaction.

### Trusted Origins and CORS

Use this working rule:

```text
Browser JavaScript making cross-origin request
→ browser enforces origin/CORS rules
→ Okta Trusted Origins may matter depending on operation

Backend server making HTTP request
→ browser CORS policy is not involved
```

This is why “Postman works, browser fails” is such a useful clue.

### Client authentication methods

#### `none`

Public client. No protected client credential.

Common with SPA/native Authorization Code + PKCE.

#### `client_secret_basic`

The secret is sent in HTTP Basic authentication to `/token`:

```http
Authorization: Basic base64(client_id:client_secret)
```

#### `client_secret_post`

The credential goes in the form body.

The client and Okta must agree on the configured method.

#### `private_key_jwt`

The client proves possession of a private key by signing a short-lived client assertion.

Conceptually:

```text
private key stays with client
       ↓
sign client assertion JWT
       ↓
/token request carries assertion
       ↓
Okta verifies against registered public key
```

Important fields:

```text
iss = client_id
sub = client_id
aud = exact token endpoint being authenticated to
exp = short-lived
kid = registered public-key identifier where applicable
```

Do not write signing crypto from scratch. Use maintained libraries. But know enough to diagnose the assertion.

### `invalid_client` is not one cause

When `/token` says `invalid_client`, check:

```text
correct client_id?
correct token endpoint?
correct auth method?
secret current/correct?
Basic vs POST mismatch?
private key matches registered public key?
kid correct?
assertion audience exact?
assertion expired?
```

### Rotation is part of implementation

A project is not complete because today's secret works.

Ask:

```text
Who owns the secret/key?
Where is it stored?
How is it rotated?
Can old/new keys overlap during rotation?
How does deployment receive the new credential?
What monitoring tells us rotation broke authentication?
```

### Lab

Create one public OIDC app and one confidential web/service app. Compare their settings side by side.

Then intentionally make the client authentication method mismatch what the client sends and prove why `/token` fails.

---
