## Day 10 — Sessions, logout, UserInfo, revocation, and the “why did it sign me back in?” ticket

### Separate all the state first

Keep this picture in your head:

```text
Okta browser session
Application session
ID token
Access token
Refresh token
```

They can influence one another, but they are not one object.

### Scenario: local app logout

The app deletes its local session:

```text
App session gone
```

But the browser may still have a valid Okta session.

Next time the app redirects to Okta:

```text
Browser -> Okta /authorize
Okta sees valid session
Okta does not need credentials again
Browser returns to app
```

The user says:

> I logged out and it logged me right back in.

Nothing mystical happened. The application session ended; the Okta SSO session did not.

### Scenario: Okta session ends

Ending the Okta browser session does not reach out and erase every JWT already issued to every API.

If a resource server is doing local JWT validation and the access token is still cryptographically valid and unexpired, it can continue to pass those local checks.

That is why session termination and token revocation/lifetime are separate concerns.

### `/userinfo`

Suppose login works but the app says the user's email is missing.

Do not jump to “authentication failed.”

Ask:

```text
Was email scope requested?
Is email expected in ID token?
Is the app expecting it from /userinfo?
Does the access token authorize /userinfo?
Is the claim configured for the token/response type?
```

The `/userinfo` endpoint is an OIDC way for the client to obtain allowed user claims using the appropriate access token.

### `/revoke`

Use revocation to tell the authorization server that a token should no longer be active.

Important behavior to understand:

```text
revoke access token
→ does not automatically revoke the related refresh token

revoke refresh token
→ associated access-token authorization is revoked at Okta
```

But if the API only performs local JWT validation, it does not call Okta to ask whether revocation occurred. An already-issued JWT can still pass local signature/issuer/audience/lifetime checks until expiration.

If immediate revocation awareness matters, introspection or another current-state design is needed.

### `/introspect`

Introspection asks the authorization server whether the token is currently active.

```text
local validation
→ fast, no Okta call for every request
→ no live revocation lookup

introspection
→ asks Okta current active state
→ network dependency/cost
```

You choose based on requirements, not because one is always universally better.

### Lab

Perform these separately:

1. Local app logout only.
2. Full Okta/browser sign-out.
3. Let access token expire.
4. Revoke access token.
5. Revoke refresh token.
6. Test the same revoked access token with local JWT validation.
7. Test it with `/introspect`.
8. Call `/userinfo` before and after changing scopes/claims.

If you can predict each result before running it, you understand the lifecycle.

---
