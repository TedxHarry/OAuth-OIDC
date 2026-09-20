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

For the core Day 12 lab, also confirm:

~~~text
Require Demonstrating Proof of Possession (DPoP) header in token requests:
Disabled
~~~

The helper implements private_key_jwt client authentication, not the separate DPoP proof flow.

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


## Part 31 - Prepare the optional write test

Only continue if this is a lab or integration tenant where a controlled group-membership change is acceptable.

Create:

~~~text
OAuth-Day12-Test-Group
~~~

Choose a disposable test user.

Record:

~~~text
Test group ID:
Test user ID:
User currently member of test group?:
~~~

Do not use a production group.

## Part 32 - Grant the write scope

On the service app, grant:

~~~text
okta.groups.manage
~~~

For the write exercise set:

~~~powershell
$env:OKTA_API_SCOPES="okta.groups.manage"
~~~

Do not grant unrelated manage scopes.

## Part 33 - Assign narrow group-membership administration

Assign:

~~~text
Group Membership Administrator
~~~

targeted to:

~~~text
OAuth-Day12-Test-Group
~~~

If your org uses custom admin roles, use an equivalent custom permission and resource-set binding limited to this test group.

The goal is:

~~~text
service can manage membership of the test group
but not arbitrary groups
~~~

Do not use Super Administrator.

## Part 34 - Add the test user to the test group

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action add-user-to-group --group-id YOUR-TEST-GROUP-ID --user-id YOUR-TEST-USER-ID --allow-write --scopes "okta.groups.manage"
~~~

Expected successful group-membership behavior:

~~~text
HTTP 204
~~~

Verify the user is now a member of:

~~~text
OAuth-Day12-Test-Group
~~~

Record:

~~~text
HTTP:
request ID:
membership verified?:
~~~

## Part 35 - Prove a resource target matters

Choose another harmless group that is not in the service app's administrative target.

Do not use a sensitive group.

Attempt:

~~~powershell
python scripts/python/day12_okta_api_client.py --action add-user-to-group --group-id OUTSIDE-TARGET-GROUP-ID --user-id YOUR-TEST-USER-ID --allow-write --scopes "okta.groups.manage"
~~~

Record:

~~~text
Token acquisition succeeded?:
Management API HTTP:
error:
~~~

Expected concept:

~~~text
scope exists
+
token issued
+
admin role exists
but
target group is outside authorized resource
-> operation denied
~~~

Do not change the key pair.

## Part 36 - Restore the test-group membership

Remove the test user from the Day 12 test group:

~~~powershell
python scripts/python/day12_okta_api_client.py --action remove-user-from-group --group-id YOUR-TEST-GROUP-ID --user-id YOUR-TEST-USER-ID --allow-write --scopes "okta.groups.manage"
~~~

Expected:

~~~text
HTTP 204
~~~

Verify the original membership state is restored.

## Part 37 - Restore least privilege after the write test

Remove temporary write capability that is no longer needed.

Restore the service app to:

~~~text
Scopes:
okta.users.read
okta.groups.read

Admin role:
Read-only Administrator

Temporary group-membership role/target:
removed if no longer required
~~~

Set:

~~~powershell
$env:OKTA_API_SCOPES="okta.users.read okta.groups.read"
~~~

Prove:

~~~text
list users works
list groups works
write capability is no longer part of the intended configuration
~~~

## Part 38 - Generate key B for rotation

Run:

~~~powershell
python scripts/python/day12_generate_keypair.py --output-dir secrets/day12-key-b
~~~

Record:

~~~text
Key A kid:
Key B kid:
Key B private path:
Key B public JWK path:
~~~

Do not remove Key A from Okta yet.

## Part 39 - Register public key B

Add Key B's public JWK to the same service app.

At this point:

~~~text
Public key A registered
Public key B registered
~~~

This is the safe overlap period.

## Part 40 - Move the automation to key B

Set:

~~~powershell
$env:OKTA_API_PRIVATE_KEY="secrets/day12-key-b/day12_private_key.pem"
$env:OKTA_API_KEY_ID="KEY-B-KID"
~~~

Run:

~~~powershell
python scripts/python/day12_okta_api_client.py --action list-users
~~~

Expected:

~~~text
token succeeds
API succeeds
~~~

Record the assertion kid.

It should be Key B.

## Part 41 - Retire key A only after Key B works

After you have proven:

~~~text
token acquisition with key B
+
Management API call with key B
~~~

you may retire public key A from the dedicated lab service app if no other process uses it.

If you manage signing keys through the Okta key-management API, deactivate key A before deleting it.

If the service app already has Okta-scoped grants, use an administrator with the required Super Admin permission for the key-rotation management action. Do not assign Super Administrator to the service app merely to make runtime API calls work.

Do not retire an old public key while an active deployment still depends on its private key.

Remember:

~~~text
add new
deploy new
prove new
retire old
~~~

## Part 42 - Explain why the token scope is not the whole answer

Use the Part 28 result.

Explain:

~~~text
The Org Authorization Server checks whether the requested scope is granted to the service app.

The Okta Management API separately checks whether the service app's assigned administrative role and resource authorization permit the operation.

Therefore a token can be issued with the scope while the API request is still denied.
~~~

## Part 43 - Troubleshoot from the last successful step

For each case, identify the last successful step.

### A

Wrong private key.

### B

okta.apps.read requested but not granted.

### C

okta.users.read token issued, but Read-only Administrator removed.

### D

okta.groups.manage token issued, but target group is outside the role target.

Expected layers:

~~~text
A -> client authentication
B -> scope grant
C -> admin authorization
D -> resource authorization
~~~

## Part 44 - Final configuration record

### Service app

~~~text
Name:
Client ID:
Client authentication:
~~~

### Current signing key

~~~text
kid:
private key path:
public JWK registered?:
~~~

Do not record key contents.

### Read scopes

~~~text
okta.users.read:
okta.groups.read:
~~~

### Current admin role

~~~text
Role:
Resource target if any:
~~~

### Org AS

~~~text
Issuer:
Token endpoint:
Assertion aud:
~~~

All three endpoint values should be internally consistent.

## Part 45 - Final behavior matrix

Complete from actual evidence.

| Test | Token issued? | API called? | Expected layer/result |
|---|---:|---:|---|
| Correct key + granted read scopes + read admin | Yes | Yes | 200 |
| Wrong assertion aud | No | No | Client authentication |
| Wrong kid | No | No | Client authentication |
| Wrong private key | No | No | Client authentication |
| Expired assertion | No | No | Client authentication |
| Replayed jti assertion | First only | No/Not needed | Client-auth replay protection |
| Supported but ungranted scope | No | No | Scope grant |
| Scope granted, admin role removed | Yes | Yes | API authorization denied |
| Manage scope + role, target outside resource | Yes | Yes | Resource authorization denied |

Explain every row.

## Part 46 - Explain the architecture to an application owner

Explain naturally:

~~~text
The automation is an Okta OAuth service app.

It does not use a human administrator session.

The automation owns a private signing key and Okta stores the matching public key.

For each token request, the automation creates a short-lived signed client assertion.

That assertion authenticates the service app to the Org Authorization Server.

The service app can request only Okta API scopes that have been granted to it.

After the token is issued, Okta Management APIs also enforce the admin role and resource access assigned to the service app.

So the OAuth scope and the administrative role are both required.

The access token is for Okta and is treated as opaque by our automation.
~~~

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Authorization server

Okta API scopes come from the Org Authorization Server.

### Client authentication

private_key_jwt proves possession of the service app's private key.

### Public/private key

Automation keeps the private key. Okta stores the public verification key.

### Client assertion

Short-lived JWT used only to authenticate the client to the token endpoint.

### Access token

Returned by the Org AS and sent as a Bearer token to Okta Management APIs.

### Scope grants

Control which Okta API scopes the service app may request.

### Admin roles

Control which administrative operations and resources the service app may actually use.

### Failure layers

Bad assertion prevents token issuance.

Ungrantable scope prevents token issuance.

Missing admin or resource permission can deny the API after token issuance succeeds.

</details>

## Day 12 completion check

You are ready for Day 13 when you can independently explain and demonstrate:

~~~text
Org Authorization Server
API Services app
private_key_jwt
public vs private key
JWK and kid
iss / sub / aud / exp / iat / jti
client assertion vs access token
Okta API scope grants
read vs manage scopes
admin roles
resource targets
scope present but API denied
safe key rotation
three-layer troubleshooting
~~~

Do not move on while scope grant and admin permission still feel like the same control.
