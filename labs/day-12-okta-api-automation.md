# Day 12 Lab - Automate Okta Management APIs

## Purpose

Day 11 proved machine-to-machine access to your own API.

Day 12 proves machine-to-machine access to Okta Management APIs.

You will build:

~~~text
Okta Management Automation
        |
        | private_key_jwt
        | Client Credentials
        v
Org Authorization Server
        |
        | okta.users.read
        | okta.groups.read
        v
Okta Management APIs
~~~

You will then break each security layer deliberately.

Complete the lesson first:

[Day 12 - Okta Management API Automation with private_key_jwt](../lessons/day-12-okta-api-automation.md)

Use the diagrams:

[Day 12 Flow Diagrams](../diagrams/day-12-okta-api-automation.md)

## Safety rules

Do not put these into GitHub, chat, tickets, screenshots, or shared notes:

~~~text
private key
full client assertion
full Okta API access token
old or new signing-key private material
~~~

Safe evidence includes:

~~~text
client ID
kid
assertion aud
assertion iat / exp
requested scope names
token response expires_in
token response scope
HTTP status
Okta request ID
operation
~~~

The repository now ignores:

~~~text
secrets/
*.pem
*.key
.env
~~~

## Part 1 - Confirm the resource you are protecting

Answer before configuring anything:

~~~text
Protected resource:
________________________

Authorization server:
________________________

Client authentication:
________________________
~~~

Expected:

~~~text
Protected resource:
Okta Management APIs

Authorization server:
Org Authorization Server

Client authentication:
private_key_jwt
~~~

Do not use the Employee API Custom Authorization Server for this lab.

## Part 2 - Record the Org Authorization Server endpoints

Your Org AS issuer is:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

The token endpoint is:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Record:

~~~text
Okta domain:
Org AS issuer:
Org AS token endpoint:
~~~

The token endpoint is also the assertion audience used later.

## Part 3 - Install the Day 12 Python dependencies

From the repository root:

~~~powershell
python -m pip install requests "PyJWT[crypto]" cryptography
~~~

## Part 4 - Generate the signing key pair locally

Run:

~~~powershell
python scripts/python/day12_generate_keypair.py
~~~

Expected local files:

~~~text
secrets/day12/day12_private_key.pem
secrets/day12/day12_public_jwk.json
~~~

Record only:

~~~text
kid:
private key path:
public JWK path:
~~~

Do not record the private-key contents.

## Part 5 - Inspect the public JWK

Open only:

~~~text
secrets/day12/day12_public_jwk.json
~~~

Identify:

~~~text
kty
kid
use
alg
n
e
~~~

Explain:

~~~text
Which field identifies this key?:

Which values represent the RSA public key?:

Is the private signing material in this file?:
~~~

Expected:

~~~text
kid identifies the key.
n and e are public RSA values.
The private key is not in the public JWK.
~~~

## Part 6 - Confirm Git will not track the private key

Run locally:

~~~powershell
git status
~~~

The files under:

~~~text
secrets/
~~~

should not appear as new files to commit.

If they appear, stop.

Do not continue until private key material is excluded.

## Part 7 - Create the API Services app

In the Okta Admin Console:

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
Okta Management Automation
~~~

Save.

Record:

~~~text
Client ID:
~~~

Do not use the Day 11 Employee Reporting Service client.

## Part 8 - Change client authentication to Public key / Private key

Open the new service app's General settings.

Edit Client Credentials.

Choose:

~~~text
Public key / Private key
~~~

Use the option that stores signing public keys in Okta.

Register the JWK from:

~~~text
secrets/day12/day12_public_jwk.json
~~~

Save.

Confirm the registered key has the same kid as the local public JWK.

The security relationship must remain:

~~~text
Okta
-> public key

automation
-> private key
~~~

## Part 9 - Explain what changed from Day 11

Complete:

| Item | Day 11 | Day 12 |
|---|---|---|
| Client authentication |  |  |
| Credential kept by automation |  |  |
| Credential registered with Okta |  |  |
| Token endpoint |  |  |
| Protected API |  |  |

Expected Day 12:

~~~text
private_key_jwt
private key
public JWK
/oauth2/v1/token on Org AS
Okta Management API
~~~

## Part 10 - Grant the read-only Okta API scopes

Open:

~~~text
Okta API Scopes
~~~

Grant:

~~~text
okta.users.read
okta.groups.read
~~~

Do not grant manage scopes yet.

Record:

~~~text
okta.users.read granted?:
okta.groups.read granted?:
~~~

## Part 11 - Assign a read-only admin role to the service app

Open the service app's Admin Roles area.

Assign:

~~~text
Read-only Administrator
~~~

The service app itself is the administrative principal.

Record:

~~~text
Service app admin role:
~~~

Do not rely on a human admin's role.

Do not assign Super Administrator merely to make the lab work.

## Part 12 - Check the Public client app admins setting

Determine whether the org setting that can automatically grant service apps Super Administrator is enabled.

Record:

~~~text
Public client app admins behavior enabled?:
~~~

If the service app has unexpected Super Administrator privilege, do not use that as proof that the least-privilege design works.

The intended lab authorization is explicit:

~~~text
Read-only Administrator
~~~

## Part 13 - Configure local environment variables

Set:

~~~powershell
$env:OKTA_DOMAIN="https://YOUR-OKTA-DOMAIN"
$env:OKTA_API_CLIENT_ID="YOUR-SERVICE-APP-CLIENT-ID"
$env:OKTA_API_PRIVATE_KEY="secrets/day12/day12_private_key.pem"
$env:OKTA_API_KEY_ID="YOUR-GENERATED-KID"
$env:OKTA_API_SCOPES="okta.users.read okta.groups.read"
~~~

Do not put the private key contents into an environment variable.

The variable contains only the local file path.

## Part 14 - Obtain the first Org AS access token

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only
~~~

Record:

~~~text
Assertion alg:
Assertion kid:
Assertion iss:
Assertion sub:
Assertion aud:
Assertion lifetime:
Token HTTP:
token_type:
expires_in:
scope:
access_token_present:
access_token_decoded:
~~~

Expected:

~~~text
iss = client ID
sub = client ID
aud = https://YOUR-OKTA-DOMAIN/oauth2/v1/token
access_token_present = True
access_token_decoded = False
~~~

## Part 15 - Explain the two credentials

Complete:

~~~text
Client assertion is sent to:
____________________

Client assertion proves:
____________________

Access token is sent to:
____________________

Access token authorizes:
____________________
~~~

Do not answer that they are the same token.

## Part 16 - List Okta users

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users
~~~

Expected:

~~~text
/token succeeds
GET /api/v1/users succeeds
~~~

Record:

~~~text
token HTTP:
Management API HTTP:
x-okta-request-id if present:
records returned:
~~~

Do not dump entire user profiles into course notes.

## Part 17 - Read one test user

Choose a known lab test user ID or login.

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action get-user --user-id YOUR-TEST-USER-ID
~~~

Record:

~~~text
HTTP:
user ID:
status:
~~~

## Part 18 - List Okta groups

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-groups
~~~

Record:

~~~text
HTTP:
records returned:
request ID:
~~~

At this point you have proven:

~~~text
private_key_jwt
+
scope grants
+
Read-only Administrator
=
read-only Okta API automation
~~~

## Part 19 - Prove one token can serve multiple API calls

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users --repeat 3
~~~

Expected summary:

~~~text
token_requests=1
api_calls=3
client_assertions_created=1
~~~

The access token is reused within the process.

Explain:

~~~text
Why is the access token reusable?:

Why should the client assertion not become the reusable API credential?:
~~~

## Part 20 - Confirm the Org AS access token stays opaque

Review the Day 12 helper.

It does not decode the access token.

Record:

~~~text
access_token_decoded=False
~~~

Explain why this differs from Day 9 and Day 11.

## Part 21 - Break the assertion audience

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault wrong-aud
~~~

The helper intentionally signs the Custom-AS token endpoint as the assertion audience while posting to the Org-AS token endpoint.

Record:

~~~text
Token issued?:
HTTP:
error:
error description:
~~~

Classify:

~~~text
Layer:
client authentication
~~~

## Part 22 - Break kid

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault wrong-kid
~~~

Record:

~~~text
Token issued?:
HTTP:
error:
~~~

Explain why changing an API scope would not repair this problem.

## Part 23 - Break the signing key

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault wrong-key
~~~

Record:

~~~text
Token issued?:
HTTP:
error:
~~~

Expected layer:

~~~text
client authentication
~~~

## Part 24 - Expire the client assertion

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault expired
~~~

Record:

~~~text
Assertion exp:
Current time approximately:
Token issued?:
OAuth error:
~~~

The failure occurs before an Okta API access token exists.

## Part 25 - Replay a client assertion

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --fault replay
~~~

The helper sends the exact same signed assertion twice.

Record:

~~~text
First token request HTTP:
Second token request HTTP:
Second request error:
~~~

Because the assertion uses a jti, the second use should be rejected as replay.

## Part 26 - Request an ungranted scope

Do not grant okta.apps.read.

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action token-only --scopes "okta.apps.read"
~~~

Record:

~~~text
Token issued?:
HTTP:
error:
~~~

This is a scope-grant failure, not a bad private key.

## Part 27 - Prove supported does not mean granted

Confirm:

~~~text
okta.apps.read
~~~

is a valid Okta API scope but is not granted to this service app.

Explain:

~~~text
Scope exists in Okta
!=
scope granted to this client
~~~

## Part 28 - Prove scope grant is not admin authorization

Keep:

~~~text
okta.users.read
~~~

granted on the service app.

Temporarily remove:

~~~text
Read-only Administrator
~~~

from the service app.

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users --scopes "okta.users.read"
~~~

Record separately:

~~~text
Did /token succeed?:
Token response scope:
Did GET /api/v1/users succeed?:
Management API HTTP:
error code/summary:
~~~

Expected concept:

~~~text
Token can still be issued because the scope is granted.

The API operation can fail because the service app lacks administrative permission.
~~~

Do not change the key.

## Part 29 - Restore the read-only admin role

Restore:

~~~text
Read-only Administrator
~~~

Run again:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users --scopes "okta.users.read"
~~~

Expected:

~~~text
token succeeds
API succeeds
~~~

## Part 30 - Explain the three layers from evidence

Complete:

| Layer | Evidence from this lab |
|---|---|
| Client authentication |  |
| Scope grant |  |
| Admin authorization |  |

Your answer should reference actual break/fix results.
