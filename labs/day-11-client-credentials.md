# Day 11 Lab - Machine-to-Machine Employee Reporting

## Purpose

This lab implements OAuth for a machine that calls another service without a human user.

The caller is:

~~~text
Employee Reporting Service
~~~

The protected endpoint is:

~~~text
GET /api/service-report
~~~

Required permission:

~~~text
employee.report.read
~~~

You will prove three different authorization layers:

~~~text
1. Can Okta authenticate the service client?
2. Can the Custom Authorization Server issue the requested service scope?
3. Does the Employee API accept the token and required scope?
~~~

Complete the lesson first:

[Day 11 - Client Credentials and Machine-to-Machine OAuth](../lessons/day-11-client-credentials.md)

Use the diagrams:

[Day 11 Flow Diagrams](../diagrams/day-11-client-credentials.md)

## Safety rules

Do not put these values into GitHub, chat, screenshots, tickets, or shared notes:

~~~text
client secret
Basic Authorization value
access token
~~~

Keep them in local environment variables or local tools.

Record:

~~~text
HTTP status
OAuth error category
issuer
audience
cid
scp
expires_in
correlation ID
~~~

instead.

## Part 1 - Confirm the Day 9 authorization server

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
Employee API Authorization Server
~~~

Record:

~~~text
Authorization Server ID:
Issuer:
Audience:
~~~

Expected audience:

~~~text
api://employee-service
~~~

We are reusing this server because the new machine caller accesses the same Employee API product.

## Part 2 - Create the service scope

Open:

~~~text
Employee API Authorization Server
  |
  v
Scopes
  |
  v
Add Scope
~~~

Create:

~~~text
Name:
employee.report.read

Display phrase:
Read employee reporting data

Description:
Allows the Employee Reporting Service to read machine reporting data
~~~

Configure the scope so it does not require interactive user consent.

For this lab:

~~~text
User consent:
Implicit

Default scope:
No
~~~

Why?

Client Credentials has no user who can approve a consent prompt.

## Part 3 - Explain the new permission before creating the client

Complete:

~~~text
employee.read
->

salary.read
->

employee.report.read
->
~~~

Expected reasoning:

~~~text
employee.read
-> normal employee endpoint permission

salary.read
-> HR salary endpoint permission

employee.report.read
-> machine reporting endpoint permission
~~~

Do not continue if employee.report.read still feels like a user group or user claim.

## Part 4 - Create the API Services application

Go to:

~~~text
Applications
  |
  v
Applications
  |
  v
Create App Integration
~~~

Choose:

~~~text
Sign-in method:
API Services
~~~

Name:

~~~text
Employee Reporting Service
~~~

Save.

Record:

~~~text
Client ID:
Client authentication method:
Client secret present?:
~~~

Do not copy the actual secret into your notes.

## Part 5 - Identify what the API Services app represents

Answer:

~~~text
Does this app represent a human employee?:

Does it need a redirect URI?:

Does it need an Okta login page?:

Can it protect a client secret?:

Is it public or confidential?:
~~~

Expected:

~~~text
No human employee
No redirect URI for Client Credentials
No login page
Yes, server process can protect credential
Confidential client
~~~

## Part 6 - Confirm the service is not using the SPA flow

The Employee Reporting Service should not require:

~~~text
/authorize
redirect URI
state
nonce
PKCE
authorization code
browser session
~~~

Write why each is absent.

The short answer is:

~~~text
No interactive user authorization transaction exists.
~~~

## Part 7 - Create a service-specific access policy

Open:

~~~text
Employee API Authorization Server
  |
  v
Access Policies
  |
  v
Add Policy
~~~

Create:

~~~text
Name:
Employee Reporting Service Access

Description:
Machine-to-machine access for the Employee Reporting Service

Assign to:
The following clients

Client:
Employee Reporting Service
~~~

Save.

Do not add the service client to the SPA policy as a shortcut.

Check the authorization server's policy order.

Confirm there is no earlier broad policy, such as an All clients policy, that can match the Employee Reporting Service before this dedicated policy. Okta stops after the first matching policy and rule.

## Part 8 - Create the Client Credentials rule

Inside the service policy add:

~~~text
Name:
Reporting Service Client Credentials
~~~

Configure:

~~~text
Grant type:
Client Credentials

User:
No user

Scopes requested:
The following scopes

employee.report.read

Access token lifetime:
15 minutes
~~~

Save.

The two most important fields are:

~~~text
Client Credentials
No user
~~~

## Part 9 - Explain why No user is required

Complete:

~~~text
Authorization Code rule can reason about:
____________________

Client Credentials rule has:
____________________
~~~

Expected:

~~~text
Authorization Code
-> authenticated human user / user assignment / groups

Client Credentials
-> no human user context
~~~

Do not assign a fake user to make the service work.

## Part 10 - Find the token endpoint through discovery

Use the Day 9 issuer:

~~~text
YOUR-DAY9-ISSUER
~~~

Open:

~~~text
YOUR-DAY9-ISSUER/.well-known/openid-configuration
~~~

Record:

~~~text
issuer:
token_endpoint:
jwks_uri:
~~~

Do not guess the token endpoint.

## Part 11 - Build the first Client Credentials request in Postman

Create:

~~~text
POST <token_endpoint>
~~~

Authorization:

~~~text
Basic Auth
~~~

Use locally:

~~~text
Username:
Employee Reporting Service client ID

Password:
Employee Reporting Service client secret
~~~

Body:

~~~text
x-www-form-urlencoded
~~~

Add:

| Key | Value |
|---|---|
| grant_type | client_credentials |
| scope | employee.report.read |

Do not add:

~~~text
openid
redirect_uri
code
code_verifier
username
password for a human user
~~~

## Part 12 - Send the successful token request

Send.

Expected response shape:

~~~text
access_token
token_type
expires_in
scope
~~~

Record only:

~~~text
HTTP:
token_type:
expires_in:
scope:
ID token returned?:
Refresh token returned?:
~~~

Expected:

~~~text
ID token:
No

Refresh token:
No
~~~

Do not copy the access token into your notes.

Keep it only in Postman for the next tests.

## Part 13 - Inspect the machine access token

You may use a local decoder or the Day 11 service client later.

Record safe claims:

~~~text
iss:
aud:
cid:
scp:
uid present?:
sub present?:
exp:
~~~

Expected core values:

~~~text
iss
-> Employee API Authorization Server

aud
-> api://employee-service

cid
-> Employee Reporting Service client ID

scp
-> includes employee.report.read
~~~

Do not require uid.

There is no user bound to this Client Credentials transaction.

## Part 14 - Start the Day 11 machine API

Open a new PowerShell terminal.

Set:

~~~powershell
$env:OKTA_API_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_API_AUDIENCE="api://employee-service"
$env:OKTA_EXPECTED_SERVICE_CLIENT_ID="YOUR-REPORTING-SERVICE-CLIENT-ID"
Remove-Item Env:DAY11_REQUIRED_SCOPE -ErrorAction SilentlyContinue
~~~

Run:

~~~powershell
python scripts/python/day11_employee_api.py
~~~

The API starts on:

~~~text
http://localhost:7100
~~~

## Part 15 - Verify the health endpoint

Call:

~~~http
GET http://localhost:7100/health
~~~

Expected:

~~~text
200
~~~

Record:

~~~text
issuer:
audience:
expected service client ID:
required scope:
~~~

The required scope should be:

~~~text
employee.report.read
~~~

## Part 16 - Call the service endpoint with no token

Send:

~~~http
GET http://localhost:7100/api/service-report
~~~

without Authorization.

Expected:

~~~text
401
~~~

Record:

~~~text
HTTP:
WWW-Authenticate:
X-Correlation-ID:
API log stage:
~~~

The request never reached scope authorization.

## Part 17 - Call the service endpoint with the Client Credentials token

Use the access token from Part 12.

Send:

~~~http
GET http://localhost:7100/api/service-report
Authorization: Bearer <machine-access-token>
~~~

Expected:

~~~text
200
~~~

Record:

~~~text
HTTP:
X-Correlation-ID:
caller cid:
caller scopes:
uid_present:
sub_present:
required_scope:
~~~

The authorization decision should be based on:

~~~text
trusted token
+
expected service cid
+
employee.report.read
~~~

not on a human username.

## Part 18 - Run the automated service client

Set:

~~~powershell
$env:OKTA_SERVICE_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_SERVICE_CLIENT_ID="YOUR-REPORTING-SERVICE-CLIENT-ID"
$env:OKTA_SERVICE_CLIENT_SECRET="YOUR-REPORTING-SERVICE-CLIENT-SECRET"
Remove-Item Env:DAY11_SERVICE_SCOPE -ErrorAction SilentlyContinue
~~~

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 3
~~~

Expected summary:

~~~text
api_calls=3
token_acquisitions=1
~~~

This proves one valid access token was reused from the in-memory cache.

Record the safe token observations printed by the client.

## Part 19 - Explain what the service client cached

The script caches in process memory:

~~~text
access token
expires_at
~~~

It does not write the token to disk.

Answer:

~~~text
Why not request a token before every API call?:

Why renew before expiration?:

Why is this cache not a production distributed-token architecture?:
~~~

## Part 20 - Break the client secret

Stop using the correct secret in a test terminal.

Set:

~~~powershell
$env:OKTA_SERVICE_CLIENT_SECRET="intentionally-wrong-secret"
~~~

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 1
~~~

Record:

~~~text
Did /token return an access token?:
HTTP:
OAuth error:
~~~

Expected category:

~~~text
client authentication failure
~~~

Restore the correct secret.

Do not change API settings for this failure.

The request failed before an API token existed.

## Part 21 - Explain invalid_client correctly

Complete:

~~~text
Last proven successful layer:

Failed layer:

Was Employee API called?:

Would changing employee.report.read fix a wrong secret?:
~~~

Expected:

~~~text
Failed at token-endpoint client authentication.
Employee API was not called.
Scope changes do not repair a wrong client credential.
~~~

## Part 22 - Request an unknown scope

Set temporarily:

~~~powershell
$env:DAY11_SERVICE_SCOPE="employee.report.does-not-exist"
~~~

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 1
~~~

Record:

~~~text
HTTP:
OAuth error:
description:
~~~

Restore:

~~~powershell
$env:DAY11_SERVICE_SCOPE="employee.report.read"
~~~

The client can authenticate, but the requested permission does not exist.

That is not the same problem as a wrong client secret.

## Part 23 - Request a real scope the service policy does not allow

The Employee API Authorization Server already has:

~~~text
salary.read
~~~

Temporarily request:

~~~powershell
$env:DAY11_SERVICE_SCOPE="salary.read"
~~~

Run the service client.

Record:

~~~text
Token issued?:
HTTP:
OAuth error:
~~~

Then restore:

~~~powershell
$env:DAY11_SERVICE_SCOPE="employee.report.read"
~~~

This proves:

~~~text
scope exists
does not mean
this service client may receive it
~~~

## Part 24 - Break the No user condition

In the service access-policy rule, temporarily replace:

~~~text
No user
~~~

with a user-oriented condition if your Admin Console permits it.

If the UI does not allow a meaningful user condition for this service rule, disable the correct No-user rule and create a temporary user-oriented rule for the same client and scope.

Do not modify the SPA policy.

Request a fresh machine token.

Record:

~~~text
Token issued?:
HTTP:
OAuth error:
~~~

Expected architecture:

~~~text
Client Credentials has no user
so
a user-oriented rule should not satisfy the request
~~~

Restore:

~~~text
User:
No user
~~~

Delete any temporary rule.

## Part 25 - Break the grant-type condition

Temporarily edit or replace the service rule so:

~~~text
Client Credentials
~~~

is not an allowed grant type.

Request:

~~~text
employee.report.read
~~~

again.

Record:

~~~text
Token issued?:
HTTP:
OAuth error:
~~~

Restore the rule:

~~~text
Grant type:
Client Credentials

User:
No user

Scope:
employee.report.read
~~~

This proves correct credentials are not enough when the policy rule does not allow the grant.

## Part 26 - Confirm the service policy is clean again

Before continuing, confirm:

~~~text
Policy:
Employee Reporting Service Access

Assigned client:
Employee Reporting Service

Rule:
Reporting Service Client Credentials

Grant:
Client Credentials

User:
No user

Scope:
employee.report.read

Temporary rules:
none

Earlier broad policy matching this service:
none
~~~

Obtain a fresh valid token again.

## Part 27 - Prove API 403 with a valid machine token

Keep a valid token containing:

~~~text
employee.report.read
~~~

Stop the Day 11 API.

Temporarily set:

~~~powershell
$env:DAY11_REQUIRED_SCOPE="employee.report.admin"
~~~

Restart:

~~~powershell
python scripts/python/day11_employee_api.py
~~~

Send the valid machine token.

Record:

~~~text
HTTP:
WWW-Authenticate:
X-Correlation-ID:
API log result:
API log stage:
~~~

Expected:

~~~text
403
insufficient_scope
~~~

Why?

~~~text
Token validation succeeded.
The API deliberately required a permission the token did not contain.
~~~

This is different from token issuance failure.

## Part 28 - Restore API authorization

Stop the API.

Run:

~~~powershell
Remove-Item Env:DAY11_REQUIRED_SCOPE -ErrorAction SilentlyContinue
python scripts/python/day11_employee_api.py
~~~

Send a fresh valid machine token.

Expected:

~~~text
200
~~~

The fix changed the endpoint authorization requirement back to the intended scope.

## Part 29 - Prove service cid validation

Stop the API.

Set:

~~~powershell
$env:OKTA_EXPECTED_SERVICE_CLIENT_ID="intentionally-wrong-client-id"
~~~

Restart.

Send a valid Employee Reporting Service token.

Expected:

~~~text
401
stage=client_id
~~~

Restore the real reporting service client ID and restart.

Expected with a fresh valid token:

~~~text
200
~~~

This proves the API is not accepting every client that can obtain a token for the audience.

## Part 30 - Prove the token is not an ID token

Review the original Client Credentials token response.

Record:

~~~text
access_token present?:
id_token present?:
refresh_token present?:
~~~

Explain:

~~~text
There is no OIDC end-user authentication event.

The service needs an OAuth access token for the resource server.
~~~

## Part 31 - Prove no browser evidence exists

For one successful automated service-client run, identify the evidence you used.

Expected:

~~~text
service process output
/token HTTP result
safe JWT observations
Employee API response
Employee API log
Okta System Log when useful
~~~

Not:

~~~text
browser callback
redirect URI
CORS
state
nonce
PKCE
~~~

Explain why Browser DevTools is not the primary diagnostic tool here.

## Part 32 - Observe token lifetime and reuse

Run:

~~~powershell
python scripts/python/day11_service_client.py --repeat 5
~~~

Record:

~~~text
expires_in:
api_calls:
token_acquisitions:
~~~

Expected in one short execution:

~~~text
one token acquisition
multiple API calls
~~~

The helper renews only when its in-memory token is missing or within 30 seconds of expiry.

## Part 33 - Reason about service restart

The helper cache is intentionally memory-only.

If the process exits:

~~~text
cached token is gone
~~~

The next process authenticates the client again and gets another token.

Answer:

~~~text
Is that OAuth failure?:
Does the service need a refresh token to recover?:
~~~

Expected:

~~~text
No.
The service can authenticate again using its client credentials.
~~~

## Part 34 - Design production credential handling

Write a production answer for:

~~~text
Where should the client secret live?:

Who can read it?:

How is it injected into the process?:

How is rotation performed?:

How is token acquisition failure alerted?:

What scopes limit the blast radius?:
~~~

Do not answer:

~~~text
hardcode it in the Python file
~~~

## Part 35 - Classify failures by layer

Fill this table.

| Symptom | First layer to investigate |
|---|---|
| /token says client authentication failed |  |
| /token rejects employee.report.does-not-exist |  |
| /token rejects salary.read for reporting service |  |
| /token fails after No user was replaced |  |
| /token fails after Client Credentials grant was removed |  |
| API returns 401 stage=client_id |  |
| API returns 403 insufficient_scope |  |
| Service receives 200 |  |

Expected categories:

~~~text
client authentication
scope definition
access policy/rule
API token validation
API scope authorization
success
~~~

## Part 36 - Compare Day 11 with Day 12 before moving on

Complete:

| Question | Day 11 | Day 12 |
|---|---|---|
| Protected resource |  |  |
| Authorization server |  |  |
| Scope type |  |  |
| Client authentication |  |  |
| Extra authorization layer |  |  |

Expected Day 11:

~~~text
Protected resource:
our Employee API

Authorization server:
Employee API Custom Authorization Server

Scope:
employee.report.read

Client authentication:
client_secret_basic

Authorization:
Custom-AS policy + Employee API scope enforcement
~~~

Do not fill Day 12 from guesswork.

The lesson only previews that Day 12 uses the Okta Org Authorization Server, Okta API scopes, private_key_jwt, and Okta administrative authorization.

Day 12 will teach and verify it in full.

## Part 37 - Correlate System Log evidence

Run:

~~~text
one successful token acquisition
one wrong-secret request
one disallowed-scope request
~~~

Use approximate timestamps to inspect Okta System Log.

Record what Okta evidence helps you establish.

Do not expect the System Log to replace:

~~~text
service HTTP response
Employee API response
Employee API correlation log
~~~

Use each evidence source for the layer it can prove.

## Part 38 - Final configuration record

### Authorization server

~~~text
Name:
ID:
Issuer:
Audience:
~~~

### Service scope

~~~text
Name:
User consent:
Default?:
~~~

### API Services app

~~~text
Name:
Client ID:
Client authentication:
Secret stored where locally?:
~~~

Do not record the secret.

### Access policy

~~~text
Policy:
Assigned client:
~~~

### Rule

~~~text
Name:
Grant:
User condition:
Allowed scope:
Access-token lifetime:
~~~

### API

~~~text
URL:
Expected issuer:
Expected audience:
Expected service client ID:
Required scope:
~~~

## Part 39 - Final behavior matrix

Complete from evidence.

| Test | Token issued? | API called? | Expected layer/result |
|---|---:|---:|---|
| Correct client + employee.report.read | Yes | Yes | 200 |
| Wrong client secret | No | No | Client authentication failure |
| Unknown scope | No | No | Scope/token request failure |
| Existing but disallowed salary.read | No | No | Policy/scope authorization failure |
| Wrong No-user rule | No | No | Policy rule mismatch |
| Client Credentials not allowed | No | No | Policy grant mismatch |
| Valid token, API requires other scope | Yes | Yes | 403 |
| Valid token, API expects other cid | Yes | Yes | 401 |

Explain each row without mentioning a user login.

## Part 40 - Explain the architecture to an application owner

Explain naturally:

~~~text
The reporting job is a machine identity, not a user session.

It authenticates to Okta with its own OAuth client credentials and requests only employee.report.read.

The Employee API Custom Authorization Server has a policy specifically for that service.

The matching rule allows Client Credentials, uses No user, and permits only the reporting scope.

Okta returns an access token.

The reporting service sends that access token to the Employee API.

The API validates the token, verifies the service client identity, and requires employee.report.read.

There is no browser, user login, ID token, or PKCE flow.
~~~

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Actor

The Employee Reporting Service acts as itself.

### Client authentication

The client ID and secret authenticate the confidential OAuth client to /token.

### Scope authorization

The Custom Authorization Server policy decides whether that client may receive employee.report.read.

### No user

Client Credentials has no human user, so the rule must match No user.

### Access token

The service receives an access token, not an ID token.

### Renewal

The service can authenticate again when it needs a new access token.

### API

The Employee API validates the service token and enforces employee.report.read.

### Troubleshooting

A token-endpoint failure and an API 403 are different layers.

</details>

## Day 11 completion check

You are ready for Day 12 when you can independently explain and demonstrate:

~~~text
machine identity
API Services app
confidential client
Client Credentials
client_secret_basic
custom service scope
No user access-policy rule
direct /token request
no browser
no ID token
no user refresh-token flow
service cid
service-token caching
API scope enforcement
invalid client vs invalid scope vs API 403
~~~

Do not move on while Client Credentials still feels like Authorization Code without the browser.
