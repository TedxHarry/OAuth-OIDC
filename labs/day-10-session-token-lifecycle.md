# Day 10 Lab - Prove Session and Token Lifecycle

## Purpose

This lab proves that the following are separate lifecycle objects:

~~~text
Okta browser session
application session
ID token
access token
refresh token
~~~

You will use two existing clients for two different jobs.

### Server-side Web Application

Used to prove:

~~~text
local application logout
vs
Okta browser-session logout
~~~

### Day 3 SPA + Day 9 Employee API Authorization Server

Used to prove:

~~~text
UserInfo
refresh token
refresh rotation
access-token revocation
refresh-token revocation
introspection
local JWT validation after revocation
~~~

Complete the lesson first:

[Day 10 - Sessions, UserInfo, Logout, Revocation, and Introspection](../lessons/day-10-session-token-lifecycle.md)

Use the diagrams:

[Day 10 Flow Diagrams](../diagrams/day-10-session-token-lifecycle.md)

## Safety rules

Do not place these values into GitHub, chat, tickets, screenshots, or shared notes:

~~~text
access token
ID token
refresh token
authorization code
PKCE verifier
client secret
session cookie
~~~

Keep them in your local tools only.

When recording results, use:

~~~text
HTTP status
active true/false
safe claims
token present yes/no
correlation ID
error category
~~~

## Part 1 - Prepare the server-side Web Application for session tests

Reuse the confidential Web Application from Day 6.

Add this Sign-in redirect URI:

~~~text
http://localhost:5100/callback
~~~

Add this Sign-out redirect URI:

~~~text
http://localhost:5100/logged-out
~~~

Confirm:

~~~text
Application type:
Web Application

Client ID:
available

Client Secret:
available
~~~

The Day 10 session app will use the Org Authorization Server:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

This part of the lab is about browser and application sessions, not our Employee API access token.

## Part 2 - Start the session lifecycle app

Install dependencies if needed:

~~~powershell
python -m pip install Flask requests "PyJWT[crypto]"
~~~

Set:

~~~powershell
$env:OKTA_ISSUER="https://YOUR-OKTA-DOMAIN"
$env:OKTA_CLIENT_ID="YOUR-WEB-CLIENT-ID"
$env:OKTA_CLIENT_SECRET="YOUR-WEB-CLIENT-SECRET"
~~~

Run:

~~~powershell
python scripts/python/day10_session_app.py
~~~

Open:

~~~text
http://localhost:5100
~~~

Use the same normal browser profile for the session tests so the browser can carry the same Okta session.

## Part 3 - Sign in to the server-side application

Click:

~~~text
Sign in with Okta
~~~

Complete authentication if prompted.

After success, record:

~~~text
Local application session active?:
Credential prompt occurred?:
Browser has day10_session cookie?:
Cookie HttpOnly?:
~~~

Do not record the cookie value.

## Part 4 - Perform Local Logout Only

Click:

~~~text
Local Logout Only
~~~

Expected application state:

~~~text
local application session removed
day10_session removed
~~~

The route does not call Okta logout.

Record:

~~~text
Application says local session absent?:
day10_session cookie removed?:
~~~

## Part 5 - Sign in again immediately

Click:

~~~text
Sign in with Okta
~~~

Observe the browser.

A valid Okta browser session can allow the authorization flow to complete without another credential prompt, depending on the authentication policy and current session state.

Record:

~~~text
Did browser reach Okta?:
Were credentials requested?:
Did local app session get recreated?:
~~~

Interpretation:

If sign-in returned quickly without a full credential prompt, that is evidence that:

~~~text
local app logout
did not end
Okta browser session
~~~

Do not treat exact prompt behavior as universal. Authentication policies, upstream IdPs, and browser state can affect what the user sees.

## Part 6 - Perform Okta browser-session logout

While signed in to the local app, click:

~~~text
Local Logout + Okta Browser Logout
~~~

The sample:

~~~text
reads the ID token needed for logout
destroys local application session
redirects browser to Okta end-session endpoint
returns to /logged-out
validates returned logout state
~~~

Record:

~~~text
Returned to /logged-out?:
Logout state matched?:
Local day10_session cookie absent?:
~~~

## Part 7 - Sign in again after Okta logout

Return to the app.

Click:

~~~text
Sign in with Okta
~~~

Record:

~~~text
Did the authorization flow behave differently from Part 5?:
Was prior Okta SSO state still sufficient?:
Was authentication required again?:
~~~

The precise prompt can depend on policy and identity-provider behavior.

The architectural point is:

~~~text
Part 4
ended only local app state

Part 6
also invoked Okta browser-session logout
~~~

## Part 8 - Prepare the SPA for refresh tokens

Open the Day 3 SPA integration.

In General Settings, confirm:

~~~text
Authorization Code:
enabled

Refresh Token:
enabled
~~~

For a SPA, Okta uses refresh-token rotation by default when refresh tokens are enabled.

Do not add a client secret.

## Part 9 - Confirm the Day 9 Employee API authorization server remains safe

Open the Day 9 authorization server and policy.

Confirm the temporary broad rule from Day 9 is gone.

Expected safe rules:

~~~text
1. HR Salary Access
2. Employee Read Access
~~~

For this Day 10 lifecycle flow, we will request:

~~~text
employee.read
~~~

plus reserved OIDC scopes.

Reserved scopes such as:

~~~text
openid
profile
email
offline_access
~~~

do not need to be created as custom scopes.

## Part 10 - Start the callback receiver

Run:

~~~powershell
python scripts/python/day03_pkce_callback_server.py
~~~

Keep it running.

## Part 11 - Obtain the Day 10 token set

Run on one line:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid profile email offline_access employee.read"
~~~

Open the generated authorization URL.

Complete sign-in.

Verify the returned state.

Exchange the fresh code in Postman.

Use the token endpoint printed by the helper.

Body:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| client_id | SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| code | fresh authorization code |
| code_verifier | matching verifier |

Do not put offline_access into the token request as a substitute for requesting it at /authorize.

It was already requested during authorization.

## Part 12 - Confirm the token response

The response should include:

~~~text
access_token
id_token
refresh_token
token_type
expires_in
scope
~~~

Record only:

~~~text
Access token present?:
ID token present?:
Refresh token present?:
Granted scope string:
expires_in:
~~~

Keep all three token values locally.

For the rest of the lab, name them:

~~~text
AT1
ID1
RT1
~~~

Do not put the actual strings into your notes.

## Part 13 - Inspect the ID token safely

Use the Day 4 decoder if helpful:

~~~powershell
python scripts/python/day04_decode_id_token.py
~~~

Record selected non-secret claims:

~~~text
iss:
aud:
sub:
name present?:
preferred_username present?:
email present?:
exp:
~~~

Remember:

~~~text
decoded
does not mean
validated
~~~

This step is only for claim comparison.

## Part 14 - Call UserInfo

Use:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action userinfo
~~~

Paste AT1 into the hidden prompt.

Record:

~~~text
HTTP status:
sub:
name:
preferred_username:
email:
email_verified if present:
~~~

Do not copy the whole response if it contains personal information you do not need in your notes.

## Part 15 - Compare ID token vs UserInfo

Create a small comparison.

| Claim | ID1 | UserInfo |
|---|---|---|
| sub |  |  |
| name |  |  |
| preferred_username |  |  |
| email |  |  |

Do not force the two columns to be identical.

Explain:

~~~text
ID-token claim placement depends on token/flow/configuration.

UserInfo returns claims authorized by the granted OIDC scopes.
~~~

## Part 16 - Start the Day 9 Employee API

Stop anything else using port 7000.

Set:

~~~powershell
$env:OKTA_API_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_API_AUDIENCE="api://employee-service"
$env:OKTA_EXPECTED_CLIENT_ID="YOUR-SPA-CLIENT-ID"
~~~

Run:

~~~powershell
python scripts/python/day09_employee_api.py
~~~

## Part 17 - Prove AT1 works at the Employee API

Send:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer AT1
~~~

Expected:

~~~text
200
~~~

Record:

~~~text
HTTP:
X-Correlation-ID:
required scope:
~~~

This proves the locally validated access token is currently usable by the API.

## Part 18 - Introspect AT1 before revocation

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action introspect-access
~~~

Paste AT1.

Record:

~~~text
HTTP:
active:
client_id:
scope:
aud:
iss:
exp:
~~~

Expected:

~~~text
active = true
~~~

Now we have two kinds of evidence before revocation:

~~~text
Local Employee API:
AT1 accepted

Okta introspection:
AT1 active
~~~

## Part 19 - Introspect RT1 before revocation

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action introspect-refresh
~~~

Paste RT1.

Record:

~~~text
HTTP:
active:
~~~

Expected:

~~~text
active = true
~~~

## Part 20 - Refresh using RT1

In Postman create:

~~~text
POST <Day 9 token endpoint>
~~~

Body:

| Key | Value |
|---|---|
| grant_type | refresh_token |
| client_id | SPA client ID |
| refresh_token | RT1 |
| scope | openid profile email offline_access employee.read |

Send.

Record:

~~~text
HTTP:
new access token present?:
new ID token present?:
refresh token returned?:
~~~

Name the returned access token:

~~~text
AT2
~~~

If a new refresh-token value is returned, name the current value:

~~~text
RT2
~~~

and stop using RT1.

If the response does not rotate to a different string in your exact configuration, record what your tenant actually returned.

Do not deliberately reuse a rotated old token outside the grace behavior.

## Part 21 - Verify the current refresh token

Introspect the current refresh token, RT2 if rotated or the current returned value otherwise.

Expected:

~~~text
active = true
~~~

This confirms which refresh credential is current before revocation tests.

## Part 22 - Prove AT2 works

Call:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer AT2
~~~

Expected:

~~~text
200
~~~

Introspect AT2 too.

Expected:

~~~text
active = true
~~~

AT2 and the current refresh token now form our working pair.

## Part 23 - Revoke only AT2

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action revoke-access
~~~

Paste AT2.

Record:

~~~text
HTTP status:
response body:
~~~

Expected revocation HTTP status:

~~~text
200
~~~

Remember:

A 200 does not prove AT2 had been active.

We prove the state separately.

## Part 24 - Introspect AT2 after revocation

Run introspection again for AT2.

Expected:

~~~text
active = false
~~~

Record the actual result.

This is server-side evidence that Okta no longer considers AT2 active.

## Part 25 - Call UserInfo with revoked AT2

Call UserInfo using AT2.

Record:

~~~text
HTTP:
response/error:
~~~

The revoked access token should no longer be accepted as an active credential by the authorization-server UserInfo endpoint.

Record the actual response rather than memorizing a specific error string.

## Part 26 - Send revoked AT2 to the Day 9 API

Important:

Do this while AT2 is still before its normal exp time.

Send:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer AT2
~~~

Our Day 9 API performs local JWT validation only.

Possible expected Day 10 result:

~~~text
200
~~~

if:

~~~text
signature valid
issuer valid
audience valid
cid valid
employee.read present
token not expired
~~~

Compare:

~~~text
Okta introspection:
active = false

Employee API:
local validation can still accept AT2
~~~

This is the central Day 10 proof.

If the token has already expired, obtain a fresh token set and repeat the access-token-revocation sequence.

## Part 27 - Explain why the revoked token can still pass locally

Write:

~~~text
What changed at Okta?:

What changed inside the JWT bytes?:

Which checks does the Employee API perform?:

Which live revocation check does the Employee API perform?:
~~~

Expected reasoning:

~~~text
Okta marked token inactive.

JWT bytes did not change.

API still checks signature/issuer/audience/time/client/scope.

API does not introspect.
~~~

## Part 28 - Prove the refresh token survived access-token revocation

Use the current refresh token to request another token set.

Body:

~~~text
grant_type=refresh_token
client_id=SPA client ID
refresh_token=current refresh token
scope=openid profile email offline_access employee.read
~~~

Expected:

~~~text
refresh succeeds
new access token returned
~~~

Name the new access token:

~~~text
AT3
~~~

Keep the newest returned refresh token as:

~~~text
RT3
~~~

This proves:

~~~text
revoking AT2
did not revoke
the refresh token
~~~

## Part 29 - Verify AT3 and RT3 are active

Introspect:

~~~text
AT3
RT3
~~~

Expected:

~~~text
AT3 active = true
RT3 active = true
~~~

Call the Employee API with AT3.

Expected:

~~~text
200
~~~

## Part 30 - Revoke RT3

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action revoke-refresh
~~~

Paste RT3.

Expected revocation HTTP status:

~~~text
200
~~~

Again, verify state separately.

## Part 31 - Introspect RT3 after revocation

Introspect RT3.

Expected:

~~~text
active = false
~~~

## Part 32 - Introspect associated AT3 after RT3 revocation

Introspect AT3.

Expected Okta behavior:

~~~text
active = false
~~~

This proves the broader refresh-token revocation behavior.

## Part 33 - Try to refresh with revoked RT3

Send a refresh request using RT3.

Record:

~~~text
HTTP:
OAuth error:
error description:
~~~

Expected:

~~~text
refresh fails
~~~

Use the actual response as evidence.

## Part 34 - Compare AT3 local API behavior after refresh-token revocation

If AT3 is still before its exp time, send it to:

~~~text
GET /api/employees
~~~

The Day 9 API may still locally accept the JWT even though introspection says inactive.

Record:

~~~text
Introspection active:
Local API HTTP:
Token expired?:
~~~

This reinforces:

~~~text
server-side revocation state
!=
pure local JWT validation state
~~~

## Part 35 - Prove Okta session logout does not revoke the Day 9 token set

For this test, obtain a fresh Day 9 Employee API access token if needed and confirm:

~~~text
introspection active = true
API = 200
~~~

Use the same browser profile for the Okta session.

Then use the Day 10 server-side session app and perform:

~~~text
Local Logout + Okta Browser Logout
~~~

After Okta browser-session logout, introspect the existing Day 9 access token again.

If you did not explicitly revoke it and it has not expired, expect it to remain active.

Call the Employee API too.

This proves:

~~~text
Okta browser-session logout
does not automatically revoke
an already-issued API access token
~~~

Record actual results.

## Part 36 - Clear a token locally without revoking it

Use a fresh token if needed.

In your local client tool, remove or stop referencing the token without calling /revoke.

Then introspect the same token value from the secure place where you retained it for this controlled test.

Expected:

~~~text
active = true
~~~

The local application forgetting a token did not change Okta's server-side token state.

If you cannot safely retain the token for this controlled comparison, skip this part rather than copying it into notes.

## Part 37 - Review refresh-token rotation without triggering reuse detection

From the refresh responses you already collected, answer:

~~~text
Did the refresh-token value rotate?:
Which value became current?:
Did you always use the newest returned token afterward?:
~~~

Do not intentionally replay an older rotated token just to generate an error.

Okta reuse detection can invalidate the current refresh token and access tokens issued since authentication.

The goal is to understand rotation, not destroy the lab state unnecessarily.

## Part 38 - Correlate System Log evidence

Review the approximate times for:

~~~text
authorization
refresh
access-token revocation
refresh-token revocation
Okta session logout
~~~

Use Okta System Log as supporting evidence.

If you did not deliberately trigger refresh-token reuse, you should not expect a reuse-detection event.

Do not force the log to contain an event you did not cause.

## Part 39 - Complete the lifecycle matrix

Fill this from your actual evidence.

| Action | App session | Okta session | Access token at Okta | Refresh token at Okta | Local JWT API |
|---|---|---|---|---|---|
| Local logout |  |  |  |  |  |
| Okta browser logout |  |  |  |  |  |
| Revoke access token |  |  |  |  |  |
| Revoke refresh token |  |  |  |  |  |
| Access token expires |  |  |  |  |  |
| Clear token locally |  |  |  |  |  |

Do not fill the table from memory before running the tests.

## Part 40 - Compare local validation and introspection

For one revoked but still-unexpired access token, record:

~~~text
Token exp still in future?:

Introspection active:

Employee API local validation result:

Why can these differ?:
~~~

Your explanation should include:

~~~text
revocation is authorization-server state

local JWT validation does not query that state
~~~

## Part 41 - Explain UserInfo to an app developer

Explain:

~~~text
UserInfo is an OIDC endpoint the client calls with an access token.

The claims it can return are based on the OIDC scopes granted to that access token.

It is not the Employee API.

It is not a replacement for the API's JWT validation.

It is useful when the client needs the full profile claims authorized by scopes such as profile and email.
~~~

## Part 42 - Explain the "logout but signed back in" ticket

Give a short diagnosis:

~~~text
The application destroyed its local session, but the Okta browser session was still active.

When the application started a new authorization request, Okta reused the existing SSO session according to policy.

If the requirement is to end the Okta browser session too, use the OIDC end-session flow and a registered post-logout redirect URI.
~~~

Then state separately whether tokens should also be removed or revoked for that application's requirement.

## Part 43 - Final evidence record

### Session app

~~~text
Local logout removed app session?:
Immediate SSO observed?:
Okta logout route used?:
Post-logout redirect succeeded?:
Logout state matched?:
~~~

### Initial lifecycle token set

~~~text
AT1 active before refresh?:
RT1 active?:
UserInfo successful?:
profile/email claims observed?:
~~~

### Refresh

~~~text
Refresh succeeded?:
AT2 issued?:
Refresh token rotated?:
Current refresh token tracked correctly?:
~~~

### Access-token revocation

~~~text
/revoke HTTP:
AT2 introspection after revoke:
UserInfo with revoked AT2:
Local API with revoked AT2:
~~~

### Refresh-token survival

~~~text
Refresh after AT2 revoke succeeded?:
AT3 issued?:
RT3 active?:
~~~

### Refresh-token revocation

~~~text
RT3 introspection:
Associated AT3 introspection:
Refresh using RT3:
Local API with still-unexpired AT3:
~~~

### Session logout vs token state

~~~text
Okta browser session ended?:
Existing Day 9 token remained active?:
Employee API token call still worked?:
~~~

## Part 44 - Final explanation

Explain this without looking:

~~~text
There is no single object called the login session.

The browser can have an Okta SSO session.

The application can have its own local session.

The client can hold ID, access, and refresh tokens.

Local logout ends the application session.

OIDC logout can end the Okta browser session.

Token revocation changes authorization-server token state.

Access-token-only revocation leaves the refresh token active.

Refresh-token revocation also revokes the associated access token at Okta.

A locally validated JWT can still pass local checks after server-side revocation because its signature, claims, and expiration did not change.

Introspection adds a live query to the authorization server.

UserInfo is a separate OIDC endpoint for user claims authorized by the access token's scopes.
~~~

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Local logout

Ends local application state only unless additional actions are deliberately implemented.

### Okta browser logout

Ends the Okta browser session through the OIDC logout flow.

It does not automatically mean every OAuth token has been revoked.

### Access-token revocation

Marks that access token inactive at the authorization server.

Its associated refresh token remains active.

### Refresh-token revocation

Revokes the refresh token and its associated access token at Okta.

### Local JWT validation

Can continue to accept a revoked but unexpired JWT because no live revocation query occurs.

### Introspection

Reports the authorization server's current active state.

### UserInfo

Returns user claims authorized by granted OIDC scopes using an access token.

### Refresh token

Allows the client to obtain new tokens without relying on the Okta browser-session cookie.

</details>

## Day 10 completion check

You are ready for Day 11 when you can predict the effect of:

~~~text
local app logout
Okta browser logout
local token deletion
access-token revocation
refresh-token revocation
access-token expiration
refresh
UserInfo
introspection
local JWT validation
~~~

and name which state object each action changes.

Do not move on while "logout" and "revoke" still feel interchangeable.
