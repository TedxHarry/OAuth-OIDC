# Day 10 - Sessions, UserInfo, Logout, Revocation, and Introspection

## Goal for today

By Day 9, you can issue the right access token and protect the right API operation.

Day 10 studies what happens after sign-in.

This is where confusing tickets begin:

> I clicked Logout, but Okta signed me back in immediately.

> We revoked the access token, but our API still accepts it.

> The ID token does not contain every profile claim I expected.

> Introspection says inactive, but local JWT validation still succeeds.

These are not contradictions.

They happen because several different pieces of state exist at the same time.

By the end of Day 10, you should understand:

- Okta browser session
- local application session
- ID token
- access token
- refresh token
- local logout
- Okta browser-session logout
- RP-initiated OIDC logout
- sign-out redirect URI
- UserInfo
- refresh-token rotation
- access-token revocation
- refresh-token revocation
- introspection
- local JWT validation vs live active-state checking
- why a revoked JWT can still pass a purely local validator
- why revoking an access token does not revoke its refresh token
- why revoking a refresh token also revokes its associated access token in Okta
- why a successful /revoke response does not prove the token had been active
- how to choose the lifecycle control the application actually needs

[Open the Day 10 flow diagrams](../diagrams/day-10-session-token-lifecycle.md)

## Separate five pieces of state

Keep these separate:

~~~text
1. Okta browser session
2. Application session
3. ID token
4. Access token
5. Refresh token
~~~

They can be related.

They are not the same object.

## Okta browser session

After a user authenticates to Okta in a browser, Okta can maintain a browser session using an Okta-specific session cookie.

Conceptually:

~~~text
Browser
   |
   | Okta session cookie
   v
Okta
~~~

That session can let Okta recognize the user during a later /authorize request.

This is what enables SSO behavior.

The exact prompts still depend on:

~~~text
session state
authentication policy
reauthentication requirements
authenticator requirements
browser cookie behavior
~~~

## Application session

A server-side Web Application can create its own session after OIDC succeeds.

Our Day 7 Web Application used:

~~~text
Browser
   |
   | opaque local application cookie
   v
Python Web Application
~~~

That cookie represented the application session.

It was not the Okta session cookie.

The application can destroy its own session without touching the Okta browser session.

## ID token

The ID token tells the OIDC client about an authentication event.

Its consumer is the OIDC client.

It has its own expiration.

Deleting a local application session does not rewrite an already-issued ID token.

Ending the Okta browser session does not rewrite an already-issued ID token either.

## Access token

The access token is the credential presented to a resource server.

Our Day 9 access token is intended for:

~~~text
aud = api://employee-service
~~~

The Employee API validates it and enforces scopes.

It has its own lifetime.

An Okta browser session can end while the access token is still unexpired.

## Refresh token

A refresh token is presented back to the authorization server to obtain new tokens without repeating the full user authorization flow.

It is not:

~~~text
an Okta browser-session cookie
an application-session cookie
an API bearer token
an ID token
~~~

A refresh token has its own lifecycle and revocation behavior.

## Several states can be active at once

At one moment:

~~~text
Okta browser session       = active
Application session        = active
ID token                   = unexpired
Access token               = unexpired
Refresh token              = active
~~~

Then the user clicks a button named:

~~~text
Logout
~~~

What should that button end?

That is an application design question.

There is no universal single object named "the session."

## Local application logout

Suppose the server-side application deletes its own session.

Now:

~~~text
Application session
-> gone

Okta browser session
-> may still exist

Access token
-> may still exist

Refresh token
-> may still exist
~~~

If the application immediately starts another OIDC authorization request:

~~~text
Browser
   |
   v
Okta /authorize
   |
   v
Okta sees existing browser session
   |
   v
user may not need to enter credentials again
   |
   v
new authorization response
~~~

The user may say:

> Logout did not work.

But local logout may have worked exactly as implemented.

The application session ended.

The Okta SSO session did not.

## Why immediate SSO happens after local logout

A common sequence is:

~~~text
1. User signs in
2. App creates local session
3. User clicks local logout
4. App destroys local session
5. App redirects to protected route
6. Protected route starts OIDC login
7. Browser reaches Okta
8. Okta browser session is still active
9. Okta returns authorization response
10. App creates a new local session
~~~

From the user's perspective:

~~~text
logout
-> immediate login
~~~

From the protocol perspective:

~~~text
local application logout succeeded
+
Okta SSO session remained active
+
application immediately initiated login again
~~~

This is a lifecycle diagnosis.

## Okta browser-session logout

If the requirement is:

> End this browser's Okta SSO session too.

the application can use the OIDC end-session/logout flow.

Okta discovery metadata provides the end-session endpoint.

A typical logout request uses:

~~~text
id_token_hint
post_logout_redirect_uri
state
~~~

Conceptually:

~~~text
Application
   |
   | redirect browser to Okta end-session endpoint
   v
Okta
   |
   | end Okta browser session
   v
registered post-logout redirect URI
~~~

The post-logout redirect URI must be registered for the application.

## Read the ID token before clearing it

If the logout flow uses:

~~~text
id_token_hint
~~~

and the ID token is in application state, read what is needed before destroying that state.

Conceptually:

~~~text
Read ID token needed for logout
        |
        v
Destroy local application session
        |
        v
Redirect browser to Okta end-session endpoint
~~~

A maintained OIDC library normally handles these details.

The Day 10 sample keeps the sequence visible for learning.

## Ending the Okta browser session is not token revocation

This is one of the most important Day 10 distinctions.

After Okta session logout:

~~~text
Okta browser session
-> ended
~~~

That does not mean every OAuth token already held by the client has automatically disappeared or been revoked.

Session logout and token revocation solve different problems.

## Lifecycle action comparison

| Action | Local app session | Okta browser session | Access token | Refresh token |
|---|---|---|---|---|
| Delete app session | Ends | Usually unchanged | Usually unchanged | Usually unchanged |
| OIDC Okta logout | App decides separately | Ends | Not automatically removed from app | Not automatically removed from app |
| Revoke access token | Unchanged | Unchanged | Revoked at authorization server | Remains active |
| Revoke refresh token | Unchanged | Unchanged | Associated access token revoked at Okta | Revoked |
| Clear token from local storage only | Unchanged | Unchanged | Server-side token state unchanged | Server-side token state unchanged |

Do not say "logout" when you mean only one row.

## UserInfo

OpenID Connect provides a UserInfo endpoint.

The client calls it with an access token:

~~~http
GET <userinfo_endpoint>
Authorization: Bearer <access_token>
~~~

The access token's granted OIDC scopes determine which standard user claims can be returned.

Examples:

~~~text
profile
email
address
phone
~~~

For code flows that issue an access token, Okta documents UserInfo as the place that contains the full set of claims for the requested OIDC scopes.

## Why UserInfo exists when we already have an ID token

Do not assume:

> I requested profile and email, so every related claim must be inside the ID token.

Claim placement depends on:

~~~text
authorization server
response type
token type
claim configuration
requested scopes
~~~

UserInfo gives the OIDC client a standards-based way to retrieve user claims authorized by the access token.

## UserInfo is not API token validation

Do not confuse:

~~~text
OIDC client calls /userinfo
~~~

with:

~~~text
Employee API validates access token
~~~

The Employee API does not call UserInfo on every request to authorize salary.read.

It validates the access token and checks the API permission.

## Compare UserInfo by scope

Transaction A:

~~~text
openid employee.read
~~~

Transaction B:

~~~text
openid profile email employee.read
~~~

The Employee API permission can remain:

~~~text
employee.read
~~~

in both.

But UserInfo can return more profile claims in Transaction B because profile and email were granted.

This is the Day 10 UserInfo exercise.

## Refresh-token setup for our SPA

To receive a refresh token in Authorization Code + PKCE:

1. The SPA app integration must allow the Refresh Token grant.
2. The authorization request must include offline_access.
3. The request must use a code-based flow.

Our Day 10 request uses:

~~~text
openid
profile
email
offline_access
employee.read
~~~

Reserved OIDC scopes do not need to be recreated as custom scopes on the Day 9 Custom Authorization Server.

## SPA refresh-token rotation

Okta uses rotating refresh tokens by default for SPAs when Refresh Token is enabled.

At a high level:

~~~text
SPA sends refresh token
        |
        v
/token
grant_type=refresh_token
        |
        v
new access token
and possibly a new refresh token value
~~~

The client must retain the current refresh token returned by the authorization server.

## Refresh-token reuse detection

Okta supports refresh-token reuse detection.

Using a rotated token again outside the configured grace behavior can cause Okta to invalidate the current refresh token and access tokens issued since authentication.

For Custom Authorization Servers, Okta emits a token-reuse System Log event when reuse is detected.

Day 10 explains this behavior.

It is not a required destructive test because it can invalidate the token family used by the rest of the lab.

## Revocation endpoint

Okta exposes a revocation endpoint for each relevant authorization server.

Use the endpoint belonging to the server that issued the token.

For the Employee API Authorization Server, derive the endpoint from discovery.

Do not copy the Org Authorization Server revocation URL into this lab.

## Revoke only the access token

Okta's documented behavior is:

~~~text
revoke access token
        |
        v
access token revoked
        |
        v
associated refresh token remains active
~~~

The refresh token may therefore still be able to obtain a new access token.

That is the defined lifecycle.

## Revoke the refresh token

Okta documents:

~~~text
revoke refresh token
        |
        +-- refresh token revoked
        |
        +-- associated access token revoked
~~~

This ends more of the authorization state than access-token-only revocation.

## A 200 from /revoke does not prove prior state

Okta returns:

~~~text
200 OK
~~~

even when the token supplied to /revoke is:

~~~text
invalid
expired
already revoked
~~~

That avoids leaking token-state information.

So this conclusion is wrong:

> /revoke returned 200, therefore I proved the token was active before revocation.

The revocation endpoint accepted the request.

Use separate evidence to test active state.

