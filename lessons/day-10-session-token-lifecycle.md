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



## Public SPA requests to lifecycle endpoints

Our Day 10 SPA is a public client.

It has:

~~~text
client_id
~~~

but no protected client secret.

For Okta introspection and revocation requests from a public client, include the client_id with the form request.

Do not invent a client secret for the SPA.

A confidential client instead authenticates according to its configured client-authentication method.

## Introspection

The authorization server exposes:

~~~text
/introspect
~~~

Introspection asks:

> What is the authorization server's current state for this token?

For an active access token, the response can contain:

~~~json
{
  "active": true,
  "scope": "...",
  "client_id": "...",
  "exp": 1234567890,
  "iss": "..."
}
~~~

For an inactive token:

~~~json
{
  "active": false
}
~~~

The exact additional fields depend on token type and state.

The key lifecycle signal is:

~~~text
active
~~~

## Local JWT validation and introspection answer different questions

### Local JWT validation

Our Day 9 Employee API validates:

~~~text
signature
issuer
audience
time
cid
scp
~~~

using public signing keys.

Question:

> Does this JWT satisfy the API's locally configured trust rules?

### Introspection

The caller asks Okta:

> Does the authorization server currently consider this token active?

Those are different questions.

## Why a revoked JWT can still pass local validation

Assume an access token is valid for 15 minutes.

At minute 2:

~~~text
signature = valid
issuer = correct
audience = correct
exp = minute 15
employee.read present
~~~

Then the access token is revoked at Okta.

The JWT bytes already held by the caller do not change.

A purely local resource server checks:

~~~text
signature
issuer
audience
exp
scope
~~~

It has no live query telling it:

~~~text
this token was revoked at minute 2
~~~

Therefore that same JWT can continue to pass the local validator until its normal expiry.

At the same time:

~~~text
/introspect
-> active = false
~~~

The results are different because the checks use different information.

## Local validation vs introspection

### Local validation advantages

~~~text
no Okta network call per API request
lower latency
works through temporary authorization-server network problems
fits short-lived JWT access tokens well
~~~

Tradeoff:

~~~text
no live revocation knowledge by itself
~~~

### Introspection advantages

~~~text
authorization server reports current active state
revocation can be observed
server can evaluate token state centrally
~~~

Tradeoffs:

~~~text
network call
latency
availability dependency
caching decisions
~~~

Do not teach:

~~~text
introspection is always better
~~~

or:

~~~text
local JWT validation is always enough
~~~

Choose based on requirements.

## Day 10 proves the revocation gap

Before access-token revocation:

~~~text
Day 9 API local validation
-> 200

/introspect
-> active = true
~~~

Then revoke only the access token.

After revocation, while the JWT is still unexpired:

~~~text
/introspect
-> active = false
~~~

but our Day 9 API can still return:

~~~text
200
~~~

because it performs local JWT validation only.

This experiment is one of the most important Day 10 exercises.

## Refresh token after access-token revocation

After access-token-only revocation:

~~~text
old access token
-> inactive at Okta

refresh token
-> still active
~~~

Use the refresh token.

A successful refresh proves:

~~~text
access-token revocation
does not revoke the refresh token
~~~

The newly issued access token is a different credential.

## Refresh-token revocation test

Later:

~~~text
revoke refresh token
        |
        v
refresh token inactive
        |
        v
associated access token inactive at Okta
        |
        v
next refresh attempt fails
~~~

If an already-issued JWT is checked only by local validation, that local result can still differ until the JWT expires.

## Clear local storage vs revoke

Suppose a SPA removes its token-manager state.

That changes:

~~~text
what this browser application currently stores
~~~

It does not automatically tell the authorization server:

~~~text
revoke this token
~~~

unless the library/application also makes a revocation request.

So:

~~~text
remove locally
!=
revoke at authorization server
~~~

This mirrors:

~~~text
local application logout
!=
Okta browser-session logout
~~~

## Expiration vs revocation

Expiration:

~~~text
current time reaches exp
        |
        v
local validator rejects token
~~~

Revocation:

~~~text
authorization server marks token inactive
before normal expiry
~~~

The words are not interchangeable.

## Session expiration is separate again

The Okta browser session can expire independently of:

~~~text
application-session lifetime
access-token lifetime
refresh-token lifetime
ID-token lifetime
~~~

When troubleshooting, name the exact object.

## Troubleshooting: logout followed by immediate SSO

Ask:

~~~text
Which local session did the app destroy?
Did it call the Okta end-session endpoint?
Was the post-logout redirect URI registered?
Did it immediately navigate to a protected route?
Did that route start /authorize again?
Was the Okta browser session still active?
~~~

Do not start with JWT signature debugging.

## Troubleshooting: profile or email missing

Ask:

~~~text
Was profile requested?
Was email requested?
Which response/token is the app reading?
Is the app expecting the claim in the ID token?
Should it use /userinfo?
What does /userinfo actually return?
~~~

A missing profile claim is not proof of failed authentication.

## Troubleshooting: revoked token still works

First define "works."

### Introspection inactive, local API still 200

~~~text
/introspect = inactive
Employee API = 200
~~~

Likely explanation:

~~~text
API performs local JWT validation
and has no live revocation check
~~~

### Introspection still active

Investigate:

~~~text
Did you revoke the correct token?
Correct authorization server?
Correct client_id?
Access token or refresh token?
Did you accidentally test a newly refreshed access token?
~~~

## Troubleshooting: revoke returned 200 but behavior did not change

Remember:

~~~text
/revoke returns 200 for invalid and already-revoked values too
~~~

A 200 alone is not proof.

Use:

~~~text
/introspect
resource request
refresh attempt
token type
issuer
client ID
~~~

to establish what changed.

## Troubleshooting: refresh stopped working

Check:

~~~text
Refresh Token grant enabled?
offline_access requested at /authorize?
correct current refresh token?
refresh token revoked?
rotation enabled?
client failed to store rotated token?
reuse detection triggered?
refresh-token lifetime or idle window?
correct authorization server?
correct client_id?
~~~

Do not automatically blame the Okta browser session.

Refresh tokens are specifically intended to obtain new tokens without depending on the browser session cookie.

## Troubleshooting: UserInfo fails

Check:

~~~text
correct authorization server's userinfo endpoint?
Bearer access token sent?
access token still active?
openid requested?
profile/email scopes granted?
wrong token type?
token from another authorization server?
~~~

Use discovery rather than guessing the endpoint path.

## A lifecycle requirement should name the desired effect

Bad requirement:

> Log the user out everywhere.

Too vague.

Ask what the business actually requires:

~~~text
Destroy only this app's local session?

End this browser's Okta SSO session?

Remove tokens from this browser?

Revoke access token at authorization server?

Revoke refresh token / authorization grant?

Force other applications to sign out too?

Require immediate API revocation awareness?
~~~

Different requirements need different controls.

## Common mistakes

### Mistake 1: Treat every state object as one session

Wrong.

Name the exact object.

### Mistake 2: Delete local app session and expect Okta SSO to disappear

Wrong.

They are separate.

### Mistake 3: End Okta browser session and assume all OAuth tokens are revoked

Wrong.

Session logout and token revocation are separate.

### Mistake 4: Clear local token storage and call the token revoked

Wrong.

Local removal is not server-side revocation.

### Mistake 5: Revoke access token and assume refresh token is revoked

Wrong.

Okta documents that the refresh token remains active.

### Mistake 6: Revoke refresh token and expect associated access token to remain active at Okta

Wrong.

Okta revokes the associated access token too.

### Mistake 7: Treat /revoke HTTP 200 as proof the token was active

Wrong.

Okta intentionally avoids revealing that state through the response.

### Mistake 8: Expect local JWT validation to know live revocation state

Wrong.

A purely local verifier has no live state query.

### Mistake 9: Introspect at the wrong authorization server

Wrong trust boundary.

Use the authorization server that issued the token.

### Mistake 10: Put a client secret into SPA lifecycle calls

Wrong.

Our SPA is public.

### Mistake 11: Expect every requested profile claim in the ID token

Wrong.

Understand claim placement and use UserInfo appropriately.

### Mistake 12: Reuse an old rotating refresh token casually

Risky.

Reuse detection can invalidate the current token family outside the configured grace behavior.

## What you should be able to explain

1. What is the Okta browser session?
2. What is the application session?
3. How are those different from ID, access, and refresh tokens?
4. Why can local logout be followed by immediate SSO?
5. What does OIDC end-session logout end?
6. Does ending the Okta browser session automatically revoke OAuth tokens?
7. What does UserInfo do?
8. Why can UserInfo contain claims not present in an ID token?
9. What does offline_access do?
10. Why are rotating refresh tokens useful for SPAs?
11. What happens when only an access token is revoked?
12. What happens to the refresh token after access-token-only revocation?
13. What happens when a refresh token is revoked?
14. Why is /revoke 200 not proof of prior token state?
15. What does introspection active mean?
16. Why can introspection say inactive while local JWT validation still succeeds?
17. What is the difference between expiration and revocation?
18. When is local validation attractive?
19. When might live introspection be required?
20. Why must a lifecycle requirement specify exactly which state should end?

## Day 10 lab

[Day 10 Lab - Prove Session and Token Lifecycle](../labs/day-10-session-token-lifecycle.md)

You will:

- enable Refresh Token on the SPA
- add a sign-out redirect URI
- obtain access, ID, and refresh tokens from the Day 9 authorization server
- compare ID-token claims with UserInfo
- refresh the token set
- observe SPA refresh-token rotation behavior
- perform local application logout only
- prove immediate SSO can occur while the Okta session remains
- perform Okta browser-session logout
- introspect an active access token
- revoke only the access token
- prove introspection becomes inactive
- prove the refresh token can still obtain a new access token
- compare revoked-token introspection with Day 9 API local JWT validation
- revoke the refresh token
- prove refresh fails afterward
- prove the associated access token becomes inactive at Okta
- correlate evidence without exposing credentials

## Day 10 completion standard

Day 10 is complete when you can draw:

~~~text
Okta browser session
Application session
ID token
Access token
Refresh token
~~~

as five separate lifecycle objects.

You must be able to predict the effect of:

~~~text
local app logout
Okta browser-session logout
clear local token storage
access-token revocation
refresh-token revocation
access-token expiration
refresh-token use
UserInfo
local JWT validation
introspection
~~~

without calling all of them "logout."

## Official references

- [Okta: OpenID Connect and OAuth 2.0](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/overview)
- [Okta: Sign users out](https://developer.okta.com/docs/guides/sign-users-out/main/)
- [Okta: Revoke tokens](https://developer.okta.com/docs/guides/revoke-tokens/main/)
- [Okta: Refresh access tokens and rotate refresh tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Okta: Manage user credentials](https://developer.okta.com/docs/concepts/manage-user-creds/)
