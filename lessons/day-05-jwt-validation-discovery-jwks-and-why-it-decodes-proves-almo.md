## Day 5 — JWT validation, discovery, JWKS, and why “it decodes” proves almost nothing

### Decoding is not validation

Anyone who has a JWT string can base64url-decode its header and payload.

That does **not** prove:

```text
who issued it
whether it was modified
whether it is for your API
whether it is expired
whether the signing key is trusted
```

So this is a bad security check:

> “I pasted the token into a decoder and it looked correct.”

### Understand the JWT shape

```text
header.payload.signature
```

Header:

```json
{
  "alg": "RS256",
  "kid": "abc123"
}
```

Payload:

```json
{
  "iss": "https://example.okta.com/oauth2/default",
  "aud": "api://employee-service",
  "sub": "00u...",
  "exp": 1780000000,
  "scp": ["employee.read"]
}
```

Signature: the part that lets the verifier detect alteration and confirm the token was signed by a trusted authorization server key.

You do not need the RSA mathematics. You need the trust chain.

### Discovery gives the client/API metadata

Start from the issuer you trust.

Conceptually:

```text
configured issuer
      ↓
OIDC discovery document
      ↓
authorization_endpoint
      token_endpoint
      jwks_uri
      userinfo_endpoint
      ...
```

The lesson is important: **configure the issuer and discover the related endpoints/keys** rather than mixing endpoints from different authorization servers or domains.

### JWKS and `kid`

Okta publishes public keys in a JWKS document.

```text
JWT header kid
      ↓
find matching JWK
      ↓
verify JWT signature
```

Libraries should cache keys and refresh them when required. If an application hardcodes one signing key forever, signing-key rotation eventually creates an `unknown kid` or signature failure.

### Validation logic

Think in this order:

```text
1. Is this structurally a token I can parse?
2. Is the signature valid with a trusted current key?
3. Is iss exactly the authorization server I trust?
4. Is aud the API/resource I am protecting?
5. Is exp still valid?
6. Is nbf valid if present?
7. Is the expected signing algorithm allowed?
```

Only then:

```text
8. Does the token contain the permission this endpoint requires?
```

Step 8 is authorization, not cryptographic token validation.

### 401 vs 403 working rule

```text
Token missing / cannot be trusted / expired
→ authentication credential unacceptable
→ typically 401

Token valid, but salary.read missing
→ caller is known/accepted but not authorized for this operation
→ typically 403
```

Use framework behavior as evidence, but keep the conceptual distinction.

### Local validation vs introspection

Local JWT validation:

```text
API
  ↓
verify JWT using cached/public keys and claims
  ↓
no network call to Okta per request
```

Introspection:

```text
API/backend
  ↓
/introspect at Okta
  ↓
current active state
```

Introspection can provide current authorization-server state, including revocation awareness, at the cost of a remote dependency/call.

### Org AS warning

Do not locally build your own API authorization around Org Authorization Server access-token contents. Those tokens are for Okta. Treat them as opaque from your application's perspective.

For your own API, use a Custom Authorization Server designed for that resource server.

### Break/fix labs

- Change expected issuer.
- Change expected audience.
- Use an expired token.
- Modify the JWT payload manually and try validation.
- Simulate/use the wrong JWKS/issuer.
- Observe behavior when the verifier sees an unknown `kid`.

For each, do not just note “validation failed.” Record **which check failed**.

### Explain-back checkpoint

You should be able to explain:

> A JWT decoder only shows me contents. Trust comes from signature validation plus issuer, audience, and lifetime checks. After the token is trusted, the API still has to make a separate authorization decision.

---
