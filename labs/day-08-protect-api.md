# Day 8 Lab - Protect the Employee API

## Purpose

This lab moves from client-side OAuth/OIDC into resource-server enforcement.

You will configure the minimum Custom Authorization Server settings required for the exercise, obtain two different access tokens, and run a real protected API.

The API endpoint is:

~~~text
GET /api/employees
~~~

Required scope:

~~~text
employee.read
~~~

You must prove all four outcomes:

~~~text
No token
-> 401

Invalid token
-> 401

Valid token without employee.read
-> 403

Valid token with employee.read
-> 200
~~~

Complete the lesson first:

[Day 8 - Protect an API: Validate First, Authorize Second](../lessons/day-08-protect-api.md)

Use the diagrams while running the lab:

[Day 8 Flow Diagrams](../diagrams/day-08-protect-api.md)

## Safety rules

Do not place any of these values into GitHub, chat, tickets, screenshots, or shared notes:

~~~text
authorization code
access token
ID token
refresh token
PKCE verifier
client secret
~~~

Record safe claims and outcomes instead.

The Employee API intentionally never logs the raw bearer token.

## Part 1 - Confirm the Custom Authorization Server exists

In the Okta Admin Console go to:

~~~text
Security
  |
  v
API
~~~

Look for:

~~~text
Authorization Servers
~~~

Find the server marked as the default Custom Authorization Server.

Its ID is normally:

~~~text
default
~~~

Do not confuse it with the Org Authorization Server.

Record:

~~~text
Authorization server name:
Authorization server ID:
Issuer:
Audience:
~~~

Typical issuer shape:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default
~~~

Use the actual values from your tenant.

## Part 2 - Understand the capability boundary before continuing

The Employee API must validate an access token intended for your own resource server.

Therefore this lab requires a Custom Authorization Server.

Do not substitute:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

as the issuer.

That is the Org Authorization Server used in earlier SSO labs.

If your org does not expose the Custom Authorization Server capability, stop the hands-on portion at this point rather than building the API around the wrong token type.

## Part 3 - Create the employee.read scope

Open:

~~~text
Security
  |
  v
API
  |
  v
Authorization Servers
  |
  v
default
  |
  v
Scopes
~~~

Add a scope.

Use:

~~~text
Name:
employee.read

Display phrase:
Read employee data

Description:
Allows read access to the Day 8 Employee API
~~~

For this training lab, do not require user consent unless you deliberately want to study consent behavior.

Do not set employee.read as a default scope.

We want the learner to explicitly request it.

## Part 4 - Check the access policy

Open:

~~~text
default Custom Authorization Server
  |
  v
Access Policies
~~~

You need an active policy and rule that can mint tokens for the Day 3 SPA client.

If an existing policy already applies to that SPA and supports the exact Day 8 tests, inspect it rather than automatically creating duplicates.

If no suitable policy exists, create one.

Suggested training policy:

~~~text
Name:
Day 8 Employee API Lab

Assign to:
The following clients

Client:
your Day 3 SPA application
~~~

Then add a rule.

Suggested rule:

~~~text
Name:
Day 8 Authorization Code Lab

Grant type:
Authorization Code

User:
a condition that includes your assigned test user

Scopes requested:
Any scopes
~~~

Keep the token-lifetime defaults for now.

Important:

~~~text
Any scopes
~~~

is intentionally broad for this lab.

We need both:

~~~text
openid employee.read
~~~

and:

~~~text
openid
~~~

to succeed so we can demonstrate 200 and 403 separately.

Do not copy this broad scope rule into a production design.

Day 9 designs the policy properly.

## Part 5 - Confirm the SPA is assigned to your test user

Open the Day 3 SPA application.

Confirm your test user can use it.

The application should still be:

~~~text
Application type:
Single-Page Application

Authorization Code:
enabled

Client authentication:
None
~~~

The registered callback from Day 3 should include:

~~~text
http://localhost:8000/callback
~~~

## Part 6 - Start the callback receiver

From the repository root:

~~~powershell
python scripts/python/day03_pkce_callback_server.py
~~~

Expected callback:

~~~text
http://localhost:8000/callback
~~~

Leave this terminal running.

## Part 7 - Prepare a token request WITH employee.read

Open another terminal.

Run on one line:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer https://YOUR-OKTA-DOMAIN/oauth2/default --client-id YOUR-SPA-CLIENT-ID --scope "openid employee.read"
~~~

The script obtains the actual authorization and token endpoints from discovery.

It prints:

~~~text
issuer
scope
state
nonce
code_verifier
code_challenge
authorization URL
token endpoint
~~~

Keep the terminal open.

Do not share the verifier.

## Part 8 - Run the authorization request

Open the generated authorization URL in a private browser window.

Complete authentication if required.

The browser returns to:

~~~text
http://localhost:8000/callback
~~~

Verify:

~~~text
authorization code present:
returned state:
expected state:
state matched:
~~~

If state does not match, stop.

Do not redeem the code.

## Part 9 - Exchange the code in Postman

Create:

~~~text
POST
https://YOUR-OKTA-DOMAIN/oauth2/default/v1/token
~~~

Use the token endpoint printed by the helper if your environment differs.

Body type:

~~~text
x-www-form-urlencoded
~~~

Add:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| client_id | Your Day 3 SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| code | Fresh authorization code |
| code_verifier | Verifier from this transaction |

Do not add:

~~~text
client_secret
~~~

The SPA is a public client.

Send the request.

Expected response fields include:

~~~text
access_token
token_type
expires_in
scope
id_token
~~~

The exact response can vary with configuration.

Do not copy the token strings into your notes.

## Part 10 - Inspect the scoped access token locally

Run:

~~~powershell
python scripts/python/day08_inspect_access_token.py
~~~

Paste the access token when prompted.

Record only these safe values:

~~~text
alg:
kid:
iss:
aud:
sub:
cid:
scp:
iat:
exp:
~~~

Confirm:

~~~text
iss
-> your default Custom Authorization Server issuer

aud
-> the audience you recorded in Part 1

cid
-> your SPA client ID

scp
-> includes employee.read
~~~

Important:

This script only decodes.

It does not validate.

The API performs actual validation.

## Part 11 - Start the Employee API

Open another PowerShell terminal.

Set:

~~~powershell
$env:OKTA_API_ISSUER="https://YOUR-OKTA-DOMAIN/oauth2/default"
$env:OKTA_API_AUDIENCE="YOUR-ACTUAL-CUSTOM-AS-AUDIENCE"
$env:OKTA_EXPECTED_CLIENT_ID="YOUR-SPA-CLIENT-ID"
~~~

Use the actual Audience value recorded in Part 1.

Start:

~~~powershell
python scripts/python/day08_employee_api.py
~~~

Expected startup output includes:

~~~text
Issuer
Audience
Expected client ID
Required scope
~~~

The API runs at:

~~~text
http://localhost:7000
~~~

## Part 12 - Verify the unprotected health endpoint

Open:

~~~text
http://localhost:7000/health
~~~

or call:

~~~http
GET http://localhost:7000/health
~~~

Expected:

~~~text
200
~~~

The health endpoint confirms that the API is running.

It does not require an access token.

## Part 13 - Test Case 1: no token

Create:

~~~http
GET http://localhost:7000/api/employees
~~~

Do not add an Authorization header.

Send.

Record:

~~~text
HTTP status:
WWW-Authenticate:
X-Correlation-ID:
response error:
API log result:
API log stage:
~~~

Expected:

~~~text
401
~~~

Reason:

~~~text
No acceptable bearer credential was supplied.
~~~

The API has not reached scope authorization.

## Part 14 - Test Case 2: malformed token

Send:

~~~http
Authorization: Bearer not-a-real-jwt
~~~

Record:

~~~text
HTTP status:
WWW-Authenticate:
X-Correlation-ID:
response error:
API log stage:
~~~

Expected:

~~~text
401
invalid_token
~~~

The token fails validation before authorization.

## Part 15 - Test Case 3: valid token WITH employee.read

Use the Custom Authorization Server access token obtained in Parts 7 through 10.

Send:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer YOUR-ACCESS-TOKEN
~~~

Expected:

~~~text
200
~~~

The response should contain sample employee data plus a safe caller summary.

Record:

~~~text
HTTP status:
X-Correlation-ID:
caller sub:
caller cid:
returned scopes:
employee count:
API log result:
~~~

Expected reasoning:

~~~text
token validation passed
employee.read was present
endpoint authorization passed
~~~

## Part 16 - Prepare a valid token WITHOUT employee.read

Start a completely new authorization transaction.

Run:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer https://YOUR-OKTA-DOMAIN/oauth2/default --client-id YOUR-SPA-CLIENT-ID --scope "openid"
~~~

Complete the browser authorization.

Compare returned state.

Exchange the fresh authorization code in Postman using its matching verifier.

You now need a valid Custom Authorization Server access token whose scp does not contain:

~~~text
employee.read
~~~

Inspect it locally:

~~~powershell
python scripts/python/day08_inspect_access_token.py
~~~

Confirm:

~~~text
iss correct:
aud correct:
cid correct:
employee.read absent:
~~~

## Part 17 - Test Case 4: valid token WITHOUT employee.read

Send the valid unscoped token to:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer YOUR-ACCESS-TOKEN
~~~

Record:

~~~text
HTTP status:
WWW-Authenticate:
X-Correlation-ID:
response error:
API log result:
API log stage:
~~~

Expected:

~~~text
403
insufficient_scope
~~~

This is the most important 401/403 comparison.

The token was accepted.

The operation was denied.

## Part 18 - Compare the four core outcomes

Complete:

| Test | Token trusted? | employee.read present? | Expected result |
|---|---:|---:|---:|
| No token | No | Not checked | 401 |
| Garbage token | No | Not checked | 401 |
| Valid token without employee.read | Yes | No | 403 |
| Valid token with employee.read | Yes | Yes | 200 |

Explain why the API must not check employee.read in the first two cases.

## Part 19 - Send the ID token to the API

Use the ID token returned from the scoped Authorization Code transaction.

Send:

~~~http
Authorization: Bearer YOUR-ID-TOKEN
~~~

Do not share the token.

Record:

~~~text
HTTP status:
X-Correlation-ID:
API validation stage:
~~~

Expected:

~~~text
401
~~~

A common reason is audience mismatch because the ID token audience represents the OIDC client, not the Employee API audience.

The exact validation stage recorded by the sample is your evidence.

Do not simply say:

> ID tokens never validate.

Say:

> This token is not acceptable for this resource-server purpose.

## Part 20 - Prove audience validation

Stop the API.

Change only:

~~~powershell
$env:OKTA_API_AUDIENCE="intentionally-wrong-audience"
~~~

Restart:

~~~powershell
python scripts/python/day08_employee_api.py
~~~

Send the previously successful scoped access token again.

Record:

~~~text
HTTP status:
X-Correlation-ID:
API validation stage:
~~~

Expected:

~~~text
401
stage=audience
~~~

Restore the actual audience and restart the API.

Send the same still-valid scoped token again.

If it has not expired, it should return:

~~~text
200
~~~

You have now proved that the audience setting caused the failure.

## Part 21 - Prove the client-ID boundary

Stop the API.

Change:

~~~powershell
$env:OKTA_EXPECTED_CLIENT_ID="intentionally-wrong-client-id"
~~~

Restart.

Send the valid scoped access token.

Expected:

~~~text
401
stage=client_id
~~~

Restore the real SPA client ID afterward.

This is a Day 8 lab restriction to one known OAuth client.

Later designs can intentionally support multiple allowed clients.

## Part 22 - Optional: compare an Org-AS access token

If you already have a current access token issued by:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

from one of the earlier labs, send it to the Employee API.

Do not obtain or expose extra credentials only for this optional step.

Expected:

~~~text
401
~~~

Reason:

~~~text
wrong issuer
wrong API trust boundary
~~~

This proves the architectural boundary taught since Day 4.

## Part 23 - Read the safe API logs

For each request, compare:

~~~text
Postman X-Correlation-ID
        |
        v
API terminal correlation_id
~~~

Example failure log shape:

~~~json
{
  "correlation_id": "...",
  "path": "/api/employees",
  "result": "invalid_token",
  "stage": "audience"
}
~~~

Example authorization failure:

~~~json
{
  "correlation_id": "...",
  "path": "/api/employees",
  "result": "insufficient_scope",
  "stage": "authorization",
  "detail": "required_scope=employee.read"
}
~~~

Confirm the log does not contain:

~~~text
full access token
ID token
refresh token
client secret
PKCE verifier
~~~

## Part 24 - Correlate token issuance with Okta System Log

Use the approximate token-issuance time and SPA application to inspect relevant Okta System Log events.

Do not expect the Okta System Log to explain your local API's 403.

The 403 is produced by your Employee API after it validates the token and checks employee.read.

Use each evidence source for what it can prove:

~~~text
Okta System Log
-> authorization/authentication/token-side events

Postman
-> actual API request and response

Access-token inspection
-> safe claim observations

Employee API log
-> validation or authorization decision
~~~

## Part 25 - Draw the API decision path

Without looking at the diagrams, draw:

~~~text
GET /api/employees
        |
        v
Bearer token?
        |
        v
signature
issuer
audience
time
cid
        |
        v
trusted token
        |
        v
employee.read?
      /     \
    no       yes
    |         |
   403       200
~~~

Add the 401 paths yourself.

Then compare with:

[Day 8 Flow Diagrams](../diagrams/day-08-protect-api.md)

## Part 26 - Evidence record

### Authorization server

~~~text
Custom AS name:
Custom AS ID:
Issuer:
Audience:
employee.read created?:
Access policy:
Policy client:
Rule grant type:
Rule scope condition:
~~~

### Scoped token

~~~text
iss:
aud:
cid:
scp:
exp:
~~~

### Unscoped token

~~~text
iss:
aud:
cid:
scp:
exp:
~~~

### API configuration

~~~text
Expected issuer:
Expected audience:
Expected client ID:
Required scope:
~~~

### Result matrix

~~~text
No token:
HTTP:
validation/authorization stage:

Garbage token:
HTTP:
validation/authorization stage:

Valid token without employee.read:
HTTP:
validation/authorization stage:

Valid token with employee.read:
HTTP:
validation/authorization stage:

ID token sent to API:
HTTP:
validation stage:

Wrong configured audience:
HTTP:
validation stage:

Wrong configured client ID:
HTTP:
validation stage:
~~~

## Part 27 - Explain the result to an application owner

Explain in less than one minute:

~~~text
The API does not trust a prior browser login by itself.

It expects an access token issued by the Custom Authorization Server for this resource.

The API first validates the token's cryptographic trust and claims.

Only after that succeeds does it check employee.read.

An invalid token returns 401.

A valid token without employee.read returns 403.

A valid token with employee.read is allowed.
~~~

Do not use the phrase:

> Okta login worked, so the API should work.

That skips the entire API authorization layer.

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Why Custom Authorization Server

The Org Authorization Server access token is intended for Okta.

Your API needs a token intended for your resource-server security boundary.

### Why audience

The API should not accept a valid token meant for some other resource audience.

### Why 401

The API could not establish an acceptable bearer credential.

### Why 403

The token was trusted, but the required permission was missing.

### Why scp is checked after validation

An unvalidated JWT payload is not trustworthy.

### Why the UI cannot enforce API security

The API can be called directly without using the frontend.

### Why correlation IDs matter

They connect the client-visible failure with the API's server-side decision without logging the bearer credential.

### Why System Log does not explain every 403

The resource server makes its own endpoint authorization decision after token issuance.

</details>

## Day 8 completion check

You are ready for Day 9 when you can explain and demonstrate:

~~~text
Org AS token vs Custom AS token
access token vs ID token at the API
issuer
audience
cid
scp
signature validation
401 invalid credential
403 insufficient permission
200 authorized request
frontend UX vs API enforcement
safe resource-server logging
~~~

Do not move on if 401 and 403 still feel interchangeable.
