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
| code_verifier | intentionally-wrong-verifier-value |

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
