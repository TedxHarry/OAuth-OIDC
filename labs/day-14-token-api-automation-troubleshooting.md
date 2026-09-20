# Day 14 Lab - Token, API, Refresh, and Automation Troubleshooting

## Purpose

Day 14 trains downstream OAuth troubleshooting.

The browser sign-in may already have succeeded.

Your first question is:

> Was a usable access token issued?

You will reuse the working systems from Days 9 through 12 and deliberately break one layer at a time.

Complete the lesson first:

[Day 14 - Token, API, Refresh, and Automation Troubleshooting](../lessons/day-14-token-api-automation-troubleshooting.md)

Keep the diagrams open:

[Day 14 Troubleshooting Diagrams](../diagrams/day-14-token-api-automation-troubleshooting.md)

## Safety rules

Never copy these into course notes or tickets:

~~~text
authorization code
PKCE verifier
client secret
private key
client assertion
access token
refresh token
ID token
~~~

Record:

~~~text
HTTP status
OAuth error
error_description
issuer
audience
client ID
kid
scope names
expires_in
validation stage
WWW-Authenticate
correlation ID
Okta request ID
System Log event
~~~

## Part 1 - Prepare the Day 14 incident template

Use this for every major failure:

~~~text
Observed symptom:

Transaction type:
Authorization server:
Grant type:

Last confirmed successful step:
First failed step:

HTTP evidence:
Safe token/assertion evidence:
API evidence:
System Log evidence:

Root cause:
Single change:
Proof after change:
~~~

## Part 2 - Confirm the systems you will reuse

You should still have these course components:

~~~text
Day 9 Employee API Authorization Server
Audience = api://employee-service

Day 9 Employee Portal SPA client

Day 11 Employee Reporting Service client
Scope = employee.report.read

Day 12 Okta Management Automation service app
private_key_jwt
~~~

Do not rebuild them just for Day 14.

Repair any configuration that was intentionally left broken in an earlier lab before beginning.

## Part 3 - Install probe dependencies

Run:

~~~powershell
python -m pip install requests "PyJWT[crypto]"
~~~

The Day 14 helper is:

~~~text
scripts/python/day14_token_probe.py
~~~

It is only for Custom Authorization Server JWT access tokens intended for APIs you own.

Do not use it to make authorization decisions from Day 12 Org-AS access tokens.

## Part 4 - Produce a fresh authorization code for a PKCE failure test

Start the Day 3 callback receiver:

~~~powershell
python scripts/python/day03_pkce_callback_server.py
~~~

In another terminal run:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid employee.read"
~~~

Open the generated authorization URL and complete the flow.

Keep locally:

~~~text
fresh code
correct code_verifier
token endpoint
~~~

Do not copy them into notes.

## Part 5 - Exchange the code with an intentionally wrong verifier

In Postman use the token endpoint from Part 4.

Body:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| client_id | your SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| code | fresh code from Part 4 |
| code_verifier | intentionally-wrong-verifier-value-0123456789-ABCDE |

Send once.

Record:

~~~text
HTTP:
error:
error_description:
usable access token issued?:
~~~

Write:

~~~text
Grant type:
Failed credential/proof:
First failed layer:
~~~

The intentionally wrong verifier is still syntactically valid PKCE input, so this exercise isolates a verifier/challenge mismatch rather than a malformed verifier.

Do not call this invalid client authentication merely because the request failed at /token.

## Part 6 - Start a completely fresh authorization transaction

The failed code from Part 5 should not become your continuing test credential.

Generate a completely new:

~~~text
state
nonce
PKCE verifier/challenge
authorization code
~~~

using the helper again.

Exchange the new code with its matching verifier.

Expected:

~~~text
/token succeeds
access token returned
~~~

Keep this employee.read access token locally as:

~~~text
EMPLOYEE_TOKEN
~~~

Do not write the token value into notes.

## Part 7 - Replay the already redeemed authorization code

Using the same code that succeeded in Part 6, send the exact code exchange again.

Record:

~~~text
HTTP:
error:
error_description:
second access token issued?:
~~~

Explain:

~~~text
First exchange:
code valid and unused

Second exchange:
same one-time grant credential reused
~~~

The correct recovery is a new authorization transaction, not repeated retries of the same code.

## Part 8 - Obtain a fresh salary token

Start another new authorization transaction:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid employee.read salary.read"
~~~

Use the HR test user from Day 9.

Exchange the fresh code correctly.

Keep the access token locally as:

~~~text
SALARY_TOKEN
~~~

## Part 9 - Start the Day 9 Employee API in its correct configuration

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

Expected endpoints:

~~~text
http://localhost:7000/api/employees
http://localhost:7000/api/salary
~~~

## Part 10 - Configure the safe Day 14 token probe

In a separate terminal set:

~~~powershell
$env:DAY14_EXPECTED_ISSUER="YOUR-DAY9-ISSUER"
$env:DAY14_EXPECTED_AUDIENCE="api://employee-service"
$env:DAY14_EXPECTED_CLIENT_ID="YOUR-SPA-CLIENT-ID"
~~~

The helper asks you to paste a token through a hidden local prompt.

The token is not echoed.

## Part 11 - Inspect EMPLOYEE_TOKEN safely

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action inspect
~~~

Paste EMPLOYEE_TOKEN locally when prompted.

Record:

~~~text
alg:
kid:
iss:
aud:
cid:
scp:
seconds_until_exp:
~~~

Also record:

~~~text
signature_validated_by_inspection=False
~~~

Explain why decoding/inspection is not validation.

## Part 12 - Check EMPLOYEE_TOKEN against the current trusted JWKS

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action jwks
~~~

Paste EMPLOYEE_TOKEN.

Record:

~~~text
expected issuer:
token issuer:
jwks_uri:
token kid:
current JWKS key count:
kid_in_current_jwks:
~~~

This is the correct starting evidence for an unknown-kid incident.

## Part 13 - Validate EMPLOYEE_TOKEN independently

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action validate
~~~

Expected:

~~~text
validation=passed
~~~

Record:

~~~text
issuer:
audience:
client ID:
scopes:
~~~

This gives you a healthy validation baseline outside the API process.

## Part 14 - Call /api/employees through the probe

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action call-api --api-url http://localhost:7000/api/employees
~~~

Paste EMPLOYEE_TOKEN.

Expected:

~~~text
200
~~~

Record:

~~~text
api_http:
X-Correlation-ID:
API log result/stage:
~~~

## Part 15 - Send a malformed bearer credential

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action call-api --api-url http://localhost:7000/api/employees --fault malformed
~~~

Paste EMPLOYEE_TOKEN.

Record:

~~~text
HTTP:
WWW-Authenticate:
correlation ID:
API validation stage:
~~~

Classify:

~~~text
token issued originally?:
resource accepted presented credential?:
401 or 403?:
~~~

## Part 16 - Simulate an unknown kid

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action call-api --api-url http://localhost:7000/api/employees --fault unknown-kid
~~~

The helper changes only the JWT header kid for the test request.

Record:

~~~text
HTTP:
API stage:
detail:
~~~

Then run:

~~~powershell
python scripts/python/day14_token_probe.py --action jwks --fault unknown-kid
~~~

Record:

~~~text
kid_in_current_jwks:
~~~

Explain why the correct response is not to disable signature validation.

## Part 17 - Simulate an invalid signature

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action call-api --api-url http://localhost:7000/api/employees --fault signature
~~~

Record:

~~~text
HTTP:
API stage:
detail:
~~~

Compare Part 16 with Part 17.

One fails while resolving the key identifier.

The other reaches signature verification with a known key relationship.

## Part 18 - Prove audience validation independently

Temporarily set in the probe terminal only:

~~~powershell
$env:DAY14_EXPECTED_AUDIENCE="api://intentionally-wrong"
~~~

Run:

~~~powershell
python scripts/python/day14_token_probe.py --action validate
~~~

Paste the unchanged valid EMPLOYEE_TOKEN.

Record:

~~~text
validation:
stage:
detail:
~~~

Restore:

~~~powershell
$env:DAY14_EXPECTED_AUDIENCE="api://employee-service"
~~~

The token did not change.

The validator trust configuration changed.

## Part 19 - Prove wrong API audience produces 401

Stop the Day 9 API.

Set:

~~~powershell
$env:OKTA_API_AUDIENCE="api://intentionally-wrong"
~~~

Restart:

~~~powershell
python scripts/python/day09_employee_api.py
~~~

Send EMPLOYEE_TOKEN to:

~~~text
GET /api/employees
~~~

Record:

~~~text
HTTP:
WWW-Authenticate:
correlation ID:
API stage:
~~~

Expected layer:

~~~text
token trust
~~~

Not:

~~~text
missing employee.read
~~~

## Part 20 - Restore the API audience and prove recovery

Stop the API.

Set:

~~~powershell
$env:OKTA_API_AUDIENCE="api://employee-service"
~~~

Restart.

If EMPLOYEE_TOKEN is still unexpired, call:

~~~text
GET /api/employees
~~~

Expected:

~~~text
200
~~~

If it expired during the exercises, obtain a fresh employee.read token rather than increasing API leeway.

## Part 21 - Prove 403 with a valid token

Send EMPLOYEE_TOKEN to:

~~~text
GET http://localhost:7000/api/salary
~~~

Expected:

~~~text
403
insufficient_scope
required scope = salary.read
~~~

Record:

~~~text
HTTP:
WWW-Authenticate:
correlation ID:
API log result/stage:
~~~

## Part 22 - Prove the same API accepts SALARY_TOKEN

Send SALARY_TOKEN to:

~~~text
GET http://localhost:7000/api/salary
~~~

Expected:

~~~text
200
~~~

If SALARY_TOKEN expired, obtain a fresh one.

Record the safe caller scopes from the API response.

## Part 23 - Write the 401 vs 403 proof

Complete:

| Test | Token validation | Permission check | Result |
|---|---|---|---|
| Wrong expected audience |  | Not reached |  |
| Unknown kid |  | Not reached |  |
| Invalid signature |  | Not reached |  |
| EMPLOYEE_TOKEN to salary endpoint |  |  |  |
| SALARY_TOKEN to salary endpoint |  |  |  |

Your explanation must use:

~~~text
trusted
not trusted
permission sufficient
permission insufficient
~~~

## Part 24 - Start the Day 11 machine baseline

Set the normal Day 11 client variables:

~~~powershell
$env:OKTA_SERVICE_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_SERVICE_CLIENT_ID="YOUR-REPORTING-SERVICE-CLIENT-ID"
$env:OKTA_SERVICE_CLIENT_SECRET="YOUR-REPORTING-SERVICE-CLIENT-SECRET"
$env:DAY11_SERVICE_SCOPE="employee.report.read"
~~~

Start the Day 11 machine API with its correct settings in another terminal:

~~~powershell
$env:OKTA_API_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_API_AUDIENCE="api://employee-service"
$env:OKTA_EXPECTED_SERVICE_CLIENT_ID="YOUR-REPORTING-SERVICE-CLIENT-ID"
Remove-Item Env:DAY11_REQUIRED_SCOPE -ErrorAction SilentlyContinue

python scripts/python/day11_employee_api.py
~~~

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 1
~~~

Expected:

~~~text
/token succeeds
/api/service-report returns 200
~~~

## Part 25 - Break only the Day 11 client secret

In the service-client terminal set:

~~~powershell
$env:OKTA_SERVICE_CLIENT_SECRET="intentionally-wrong-secret"
~~~

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 1
~~~

Record:

~~~text
Did /token issue a token?:
HTTP:
OAuth error:
Was /api/service-report called?:
~~~

Restore the correct secret.

Classify this before changing API settings.

## Part 26 - Request an unknown service scope

Set:

~~~powershell
$env:DAY11_SERVICE_SCOPE="employee.report.does-not-exist"
~~~

Run the service client.

Record:

~~~text
client authentication reached?:
token issued?:
HTTP:
OAuth error:
~~~

Restore:

~~~powershell
$env:DAY11_SERVICE_SCOPE="employee.report.read"
~~~

## Part 27 - Request a real but disallowed service scope

Temporarily set:

~~~powershell
$env:DAY11_SERVICE_SCOPE="salary.read"
~~~

Run the service client.

The scope exists on the authorization server but should not be permitted by the reporting-service policy.

Record:

~~~text
token issued?:
HTTP:
OAuth error:
~~~

Restore employee.report.read.

Explain:

~~~text
scope exists
!=
service client may receive it
~~~


## Part 28 - Prove token issued but machine API can still return 401

Keep the Day 11 service client correct.

Stop the Day 11 API.

Temporarily set:

~~~powershell
$env:OKTA_EXPECTED_SERVICE_CLIENT_ID="intentionally-wrong-client-id"
~~~

Restart:

~~~powershell
python scripts/python/day11_employee_api.py
~~~

Run the normal Day 11 service client.

Record separately:

~~~text
Did /token succeed?:
Did API receive a bearer token?:
API HTTP:
API validation stage:
~~~

Expected classification:

~~~text
token issuance succeeded
resource trust failed
~~~

Restore the real reporting-service client ID and restart the API.

## Part 29 - Prove token issued but machine API can return 403

Stop the Day 11 API.

Set:

~~~powershell
$env:DAY11_REQUIRED_SCOPE="employee.report.admin"
~~~

Restart.

Run the normal service client requesting:

~~~text
employee.report.read
~~~

Record:

~~~text
/token succeeded?:
API HTTP:
WWW-Authenticate:
API result/stage:
~~~

Expected:

~~~text
403
insufficient_scope
~~~

Restore:

~~~powershell
Remove-Item Env:DAY11_REQUIRED_SCOPE -ErrorAction SilentlyContinue
~~~

Restart and prove 200 again.

## Part 30 - Compare the four Day 11 failure locations

Complete:

| Failure | Token issued? | API called? | Result layer |
|---|---:|---:|---|
| Wrong client secret |  |  |  |
| Unknown/disallowed scope |  |  |  |
| Wrong expected service cid |  |  |  |
| API requires missing scope |  |  |  |

Your explanation should distinguish:

~~~text
client authentication
token-issuance authorization
resource trust
resource authorization
~~~

## Part 31 - Prepare a fresh refresh-token authorization

Use the Day 9 SPA client.

Confirm its app configuration allows:

~~~text
Authorization Code
Refresh Token
~~~

Start the callback receiver if needed.

Generate a fresh authorization request:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid profile email offline_access employee.read"
~~~

Complete sign-in.

Exchange the fresh code correctly at the Day 9 token endpoint.

Keep locally:

~~~text
AT1 = returned access token
RT1 = returned refresh token
~~~

Do not put either token into notes.

## Part 32 - Prove the fresh access and refresh tokens are active

Use:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action introspect-access
~~~

Paste AT1 through the hidden prompt.

Then run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action introspect-refresh
~~~

Paste RT1.

Record only:

~~~text
AT1 active:
RT1 active:
~~~

## Part 33 - Call the local Employee API with AT1

Ensure the Day 9 API is running normally on port 7000.

Call:

~~~text
GET /api/employees
Authorization: Bearer AT1
~~~

Expected:

~~~text
200
~~~

Record the correlation ID.

This establishes local validation before revocation.

## Part 34 - Revoke only AT1

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action revoke-access
~~~

Paste AT1.

Remember:

~~~text
/revoke HTTP 200
!=
proof of previous token state
~~~

Use introspection next.

## Part 35 - Prove AT1 is inactive at Okta

Run introspection again for AT1.

Record:

~~~text
active:
~~~

Expected:

~~~text
false
~~~

Now, if AT1 is still before exp, call the local Day 9 API with the same AT1.

Record:

~~~text
introspection active:
local API HTTP:
~~~

A possible result is:

~~~text
active=false
local API=200
~~~

because the local API checks JWT trust locally and does not perform live revocation lookup.

If AT1 expired before this test, record that and do not extend its lifetime just to force the demonstration.

## Part 36 - Prove RT1 survives access-token-only revocation

Use RT1 at the Day 9 token endpoint.

Postman body:

| Key | Value |
|---|---|
| grant_type | refresh_token |
| client_id | SPA client ID |
| refresh_token | current RT1 |
| scope | openid profile email offline_access employee.read |

No client secret.

Record:

~~~text
HTTP:
new access token returned?:
refresh token returned?:
~~~

Keep:

~~~text
AT2 = newest access token
RT2 = newest/current refresh token
~~~

If Okta does not return a new refresh-token string in that response, continue treating the current valid refresh token according to the actual response and configured rotation/lifetime behavior.

The important proof is:

~~~text
access-token-only revocation
did not revoke the refresh capability
~~~

## Part 37 - Revoke the current refresh token

Run:

~~~powershell
python scripts/python/day10_lifecycle_client.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --action revoke-refresh
~~~

Paste the current RT2.

Then introspect that refresh token.

Record:

~~~text
refresh active after revocation:
~~~

## Part 38 - Attempt refresh after refresh-token revocation

Send another refresh request using the revoked current refresh token.

Record:

~~~text
HTTP:
error:
error_description:
new access token issued?:
~~~

Classify:

~~~text
grant type:
credential being rejected:
first failed layer:
~~~

Do not call it an API 401.

The resource API was not reached.

## Part 39 - Review refresh rotation without replaying a live old token

Do not deliberately replay an old rotating refresh token from a useful authorization family.

Write the expected investigation if reuse detection occurs:

~~~text
Which refresh-token string did client store?
Was a newer refresh token returned?
Was the older token reused outside grace behavior?
What is the configured grace period?
Did System Log record reuse detection?
Were newer refresh/access tokens invalidated?
~~~

Current Okta event names include:

~~~text
app.oauth2.as.token.detect_reuse
-> Custom Authorization Server

app.oauth2.token.detect_reuse
-> Org Authorization Server
~~~

This part is a troubleshooting exercise, not a destructive replay test.

## Part 40 - Record the refresh failure matrix

| Test | Access token state | Refresh token state | Expected result |
|---|---|---|---|
| Fresh AT1 + RT1 |  |  | API and refresh work |
| Revoke AT1 only |  |  | RT can still refresh |
| Revoke current RT |  |  | Refresh fails |
| Reuse-detection event | Depends | Token family impacted | Investigate rotation/replay |

Explain why these are different lifecycle states.

## Part 41 - Restore the Day 12 Okta API automation baseline

Use the working Day 12 environment:

~~~powershell
$env:OKTA_DOMAIN="https://YOUR-OKTA-DOMAIN"
$env:OKTA_API_CLIENT_ID="YOUR-SERVICE-APP-CLIENT-ID"
$env:OKTA_API_PRIVATE_KEY="YOUR-CURRENT-DAY12-PRIVATE-KEY-PATH"
$env:OKTA_API_KEY_ID="YOUR-CURRENT-DAY12-KID"
$env:OKTA_API_SCOPES="okta.users.read okta.groups.read"
~~~

Confirm the service app has:

~~~text
public key matching current private key
okta.users.read
okta.groups.read
Read-only Administrator
~~~

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users
~~~

Expected:

~~~text
/token succeeds
Management API succeeds
~~~

## Part 42 - Break private_key_jwt authentication

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault wrong-key
~~~

Record:

~~~text
Did Org AS issue access token?:
HTTP:
OAuth error:
~~~

Classify:

~~~text
Day 12 layer:
client authentication
~~~

Do not inspect admin roles first.

## Part 43 - Request an Okta API scope that is not granted

Assuming okta.apps.read is not granted to this service app, run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --scopes "okta.apps.read"
~~~

Record:

~~~text
token issued?:
HTTP:
OAuth error:
~~~

Classify:

~~~text
Day 12 layer:
scope grant
~~~

Do not change the private key.

## Part 44 - Prove granted scope is still not admin permission

This is a controlled configuration test.

Keep:

~~~text
okta.users.read
~~~

granted to the service app.

If you can safely edit the dedicated Day 12 lab service app, temporarily remove:

~~~text
Read-only Administrator
~~~

Then run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users --scopes "okta.users.read"
~~~

Record separately:

~~~text
/token HTTP:
scope returned:
Management API HTTP:
error code/summary:
~~~

Expected architecture:

~~~text
scope grant can allow token issuance
while
missing admin permission can deny the API operation
~~~

Restore Read-only Administrator immediately and prove list-users works again.

If you cannot safely mutate the role assignment, reuse the evidence you captured in Day 12 and explain the same layer boundary.

## Part 45 - Compare Day 12 failure layers

Complete:

| Failure | Token issued? | Management API reached? | Layer |
|---|---:|---:|---|
| Wrong private key |  |  |  |
| Ungranted okta.apps.read |  |  |  |
| Granted okta.users.read, admin role missing |  |  |  |
| Correct scope + role |  |  |  |

Your explanation must not collapse scope grant and admin role into one control.

## Part 46 - Build a dev-vs-prod token/API comparison

Create this table for an imagined production deployment.

| Setting | Dev | Prod | Match required or intentionally different? |
|---|---|---|---|
| Authorization server issuer |  |  |  |
| Authorization server ID |  |  |  |
| Audience |  |  |  |
| Client ID |  |  |  |
| Client auth method |  |  |  |
| Secret/key/kid |  |  |  |
| Scope definitions |  |  |  |
| Access-policy order |  |  |  |
| Expected API cid |  |  |  |
| JWKS URI |  |  |  |
| Token lifetime |  |  |  |
| Refresh behavior |  |  |  |
| Admin role/resource targets |  |  |  |
| API base URL |  |  |  |
| Host clock synchronized |  |  |  |

For every difference mark:

~~~text
intentional
or
candidate defect
~~~

## Part 47 - Diagnose environment-pairing failures

For each case identify the expected first failure.

### A

~~~text
Prod client ID
+
Dev client secret
~~~

### B

~~~text
Prod API
+
Dev Custom-AS token
+
different audience
~~~

### C

~~~text
Prod service app client ID
+
Dev private key
~~~

### D

~~~text
Prod token
+
API pinned to stale/wrong issuer JWKS
~~~

Use these categories:

~~~text
client authentication
token trust
key/JWKS resolution
~~~

## Part 48 - Expiry and clock reasoning

Use the Day 14 probe against a current Custom-AS token:

~~~powershell
python scripts/python/day14_token_probe.py --action inspect
~~~

Record:

~~~text
iat:
exp:
seconds_until_exp:
~~~

Answer:

~~~text
What should the client do before expiry?:

If token is already expired, should API increase leeway just to accept it?:

If many fresh tokens look not-yet-valid or expired immediately, what infrastructure condition should be checked?:
~~~

Expected investigation includes system clock synchronization.

## Part 49 - Decide retry vs alert

Classify each.

| Failure | Retry automatically? | Why? |
|---|---|---|
| invalid_client |  |  |
| wrong audience |  |  |
| unknown scope |  |  |
| missing admin role |  |  |
| network timeout |  |  |
| temporary server 5xx |  |  |
| rate limit |  |  |

Do not answer every row with retry.

Configuration failures need correction.

Transient failures may use bounded retry/backoff.

## Part 50 - Diagnose from symptoms only

For each symptom identify the first layer to investigate.

### A

~~~text
POST /token returns client authentication error.
No access token exists.
~~~

### B

~~~text
Authorization Code exchange fails only when verifier is changed.
~~~

### C

~~~text
Token probe validates signature and issuer but reports audience failure.
~~~

### D

~~~text
Employee API returns 403 and WWW-Authenticate says insufficient_scope.
~~~

### E

~~~text
JWT kid is absent from cached keys and also absent after refreshing the trusted issuer JWKS.
~~~

### F

~~~text
Refresh token was revoked and later refresh request fails.
~~~

### G

~~~text
Day 11 /token succeeds but machine API reports unexpected cid.
~~~

### H

~~~text
Day 12 token response includes okta.users.read but Users API operation is denied.
~~~

### I

~~~text
Dev works. Prod uses a different issuer/audience pair.
~~~

### J

~~~text
One service retries invalid_client every second for hours.
~~~

Write:

~~~text
last successful step
first failed layer
first evidence to inspect
one thing NOT to change
~~~

for each.

## Part 51 - Write four complete incident notes

Choose four different categories:

~~~text
one /token grant failure
one resource 401
one resource 403
one refresh failure
one Client Credentials failure
one Okta API admin-authorization failure
~~~

For each use the Day 14 incident template.

At least one note must include a correlation ID or Okta request ID.

## Part 52 - Final behavior matrix

Complete from evidence.

| Scenario | Token issued? | Resource trusts token? | Permission sufficient? | Result layer |
|---|---:|---:|---:|---|
| Wrong PKCE verifier | No | N/A | N/A |  |
| Reused code | No | N/A | N/A |  |
| Wrong Day 11 secret | No | N/A | N/A |  |
| Unknown service scope | No | N/A | N/A |  |
| Unknown JWT kid | Yes originally | No | N/A |  |
| Wrong audience | Yes | No | N/A |  |
| Valid employee token to salary | Yes | Yes | No |  |
| Valid salary token to salary | Yes | Yes | Yes |  |
| Revoked refresh token used at /token | No new token | N/A | N/A |  |
| Day 12 wrong private key | No | N/A | N/A |  |
| Day 12 ungranted scope | No | N/A | N/A |  |
| Day 12 scope granted, admin role missing | Yes | Okta accepts bearer token | No admin permission |  |

Explain every row without using only the word OAuth.

## Part 53 - Final explain-back

Explain this from memory:

~~~text
My first question is whether the authorization server issued a usable access token.

If no token exists, I troubleshoot the token endpoint: endpoint, client authentication, grant, then scope or policy.

If a token exists and my API returns 401, I troubleshoot token trust: type, kid/JWKS, signature, issuer, audience, time, and client boundary.

If the API trusts the token but returns 403, I troubleshoot the permission required by the operation.

invalid_grant is not one root cause. I first identify whether the credential is an authorization code, refresh token, or another grant credential.

An unknown kid makes me refresh the JWKS from the trusted issuer. It does not make me disable signature validation.

A rotating refresh token must be tracked carefully. I do not casually replay old refresh tokens because reuse detection can invalidate the authorization family.

For Client Credentials there is no browser user to troubleshoot.

For Okta Management APIs, private_key_jwt authentication, OAuth scope grants, and admin/resource authorization are separate layers.

Dev and prod can run identical code and still fail differently because issuer, audience, clients, keys, policies, scopes, and roles are deployment configuration.

I change one relevant control and prove the same transaction succeeds afterward.
~~~

## Day 14 completion check

You are ready for Day 15 when you can receive a token/API incident without being told the category and produce:

~~~text
transaction
grant
last successful step
first failed layer
safe evidence
root cause
one change
proof
~~~

Do not move on if a 401, 403, invalid_client, invalid_grant, and invalid_scope still feel like variations of the same error.
