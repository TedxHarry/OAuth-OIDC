## Day 3 — Authorization Code + PKCE: understand why every piece exists

### Start with the problem PKCE solves

Suppose the application starts an authorization flow and receives:

```text
https://app.example.com/callback?code=ABC123
```

The code is intentionally short-lived and one-time, but imagine another party manages to intercept it before the legitimate client redeems it.

If possession of the code alone were enough, the attacker could try:

```text
stolen code
   |
   v
/token
   |
   v
access token
```

PKCE adds a second piece that the legitimate client created before the authorization request.

### The verifier/challenge logic

The client generates a high-entropy random value:

```text
code_verifier = secret random value for this transaction
```

It derives:

```text
code_challenge = BASE64URL(SHA256(code_verifier))
```

The authorization request carries the challenge, not the verifier:

```text
Client/Browser -> Okta /authorize
                   code_challenge=...
                   code_challenge_method=S256
```

Later, the token request sends the verifier:

```text
Client -> Okta /token
          code=ABC123
          code_verifier=<original value>
```

Okta derives the challenge from that verifier and compares it with what was bound to the authorization request.

```text
SHA256(received code_verifier)
             ==
original code_challenge ?
```

If not, the code cannot be redeemed through that PKCE transaction.

The point is not to memorize a hash formula. The point is:

> The authorization code is not enough by itself. The client must also prove possession of the verifier created for that flow.

### Understand `state` separately

`state` is not PKCE.

The application generates a value before redirecting to Okta and expects the same value back.

```text
App creates state = X
        ↓
/authorize?...state=X
        ↓
callback?...state=X
        ↓
App compares expected vs returned
```

That helps bind the browser response to the browser transaction the application initiated and protects against request-forgery style problems.

If the application generated `state=A` but receives `state=B`, do not continue just because a valid-looking code is present.

### Understand `nonce` separately

`nonce` belongs to the OIDC identity side.

The client sends it in the authorization request. The resulting ID token should be tied back to that request through the nonce value.

Think:

```text
state → protect/correlate authorization response transaction
nonce → bind OIDC ID-token response to authentication request
PKCE  → protect authorization-code redemption
```

They are related to the same flow but solve different problems.

### The full flow

```text
1. Client generates state, nonce, code_verifier
2. Client derives code_challenge
3. Browser -> Okta /authorize
4. User authenticates
5. Okta evaluates policies/authorization request
6. Okta -> browser -> callback?code=...&state=...
7. Client verifies state
8. Client -> /token with code + code_verifier
9. Confidential client also authenticates itself if configured
10. Okta returns applicable tokens
11. Client validates the OIDC response/ID token
```

### Public and confidential clients

For a SPA:

```text
client authentication = none
PKCE                  = yes
```

For a confidential web app:

```text
client authentication = client secret/private key
PKCE                  = also usable/recommended
```

Do not think client authentication and PKCE are substitutes.

```text
client authentication → proves the client identity
PKCE                  → binds code redemption to the initiating client transaction
```

### Build the request manually once

Use an SDK in production, but during training inspect or manually construct:

```http
GET https://{yourOktaDomain}/oauth2/default/v1/authorize?
 client_id=...
 &response_type=code
 &redirect_uri=http://localhost:3000/callback
 &scope=openid%20profile%20email
 &state=...
 &nonce=...
 &code_challenge=...
 &code_challenge_method=S256
```

After the callback, inspect:

```text
code
state
```

Then inspect the token request.

### Break/fix labs

Break one at a time:

**Wrong verifier**

Expected reasoning:

```text
/authorize succeeded
callback contains code
/token fails
→ investigate code redemption/PKCE
```

**Reused authorization code**

First exchange succeeds, second fails.

**Wrong redirect URI at token exchange**

The URI must stay consistent with the authorization transaction where required.

**Wrong `state`**

The client should reject the browser response rather than blindly continuing.

**Wrong `nonce`**

The OIDC response should fail the client's nonce validation.

### Explain-back checkpoint

You should be able to explain PKCE without saying “because OAuth requires it.” Explain the attack/problem first, then the mechanism.

---
