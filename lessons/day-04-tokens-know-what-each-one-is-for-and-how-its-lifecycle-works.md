## Day 4 — Tokens: know what each one is for and how its lifecycle works

### Start with three different consumers

A common beginner mistake is treating every token as “the OAuth token.” Stop doing that now.

```text
ID token      → client application
Access token  → resource server/API
Refresh token → authorization server
```

The easiest way to understand them is to ask:

> Who is supposed to consume this token, and what question are they trying to answer?

### ID token

The application wants to know about the authentication event/user.

A simplified payload might contain:

```json
{
  "iss": "https://example.okta.com/oauth2/default",
  "sub": "00u123...",
  "aud": "0oaClientId...",
  "exp": 1780000000,
  "iat": 1779996400,
  "nonce": "...",
  "email": "user@example.com"
}
```

Notice the audience: for an ID token, the client application is the intended audience.

### Access token

The API needs a credential representing granted access.

The client sends it like this:

```http
GET /api/profile
Authorization: Bearer eyJ...
```

For an access token minted by a Custom Authorization Server for your API, the API validates it and then checks the appropriate scopes/claims.

Never build an API that accepts an ID token just because “it is also a JWT.” Correct token type and audience matter.

### Refresh token

Access tokens should not need to live forever just so the user avoids signing in every hour.

The refresh token solves that lifecycle problem:

```text
Access token expires
        ↓
Client sends refresh token to /token
        ↓
New access token
        ↓
Possibly new refresh token when rotation is used
```

The refresh token is powerful precisely because it can outlive an access token. Treat it as a sensitive credential.

### `offline_access` — understand what it does

If an Authorization Code/OIDC client needs refresh-token capability, request:

```text
offline_access
```

in the authorization request, assuming the app and policy are configured to permit refresh tokens.

A typical scope set could be:

```text
openid profile email offline_access employee.read
```

Do not assume that checking “Refresh Token” in the app configuration automatically means every authorization response will contain one.

### Refresh-token rotation

With rotation, the client uses refresh token R1:

```text
R1 -> /token -> access token A2 + refresh token R2
```

Now R2 is the token to keep using. Reuse of an old rotating token can indicate replay/compromise and trigger Okta's reuse-detection behavior.

The important engineering lesson is not to memorize every lifetime. Learn where lifetimes and rotation are configured and how your client library handles token replacement.

### Client Credentials is different

For a machine-to-machine Client Credentials integration, there is no user session to extend. The service normally requests a new access token when the existing one expires.

Think:

```text
service credential
      ↓
/token grant_type=client_credentials
      ↓
short-lived access token
      ↓
cache until near expiry
      ↓
request another access token
```

Do not design M2M around the user refresh-token pattern.

### Inspect real tokens

Decode a real ID token and Custom-AS access token. Find:

```text
iss
sub
aud
exp
iat
scp
kid (header)
```

Do not interpret a claim just because you recognize its name. Ask what component is expected to consume that token.

### Break/fix labs

1. Remove `offline_access` and observe the token response.
2. Let an access token expire and call the API again.
3. Use the refresh token to obtain another access token.
4. Enable/use rotation and inspect the refresh-token replacement behavior.
5. Revoke the refresh token and test what happens next.

### Explain-back checkpoint

You should be able to answer:

> Why not just make the access token valid for a week?

A good answer talks about limiting exposure, short-lived API credentials, and using the refresh lifecycle when continued access is appropriate.

---
