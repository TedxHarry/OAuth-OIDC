# Day 12 - Okta Management API Automation with private_key_jwt

## Goal for today

Day 11 taught machine-to-machine OAuth for your own API.

Day 12 uses Client Credentials again, but the protected resource is different:

~~~text
Okta Management APIs
~~~

That changes the authorization server, scopes, client authentication, and authorization model.

By the end of Day 12, you should understand:

- why Okta Management API automation uses the Org Authorization Server
- why a Custom Authorization Server is wrong for Okta API scopes
- why OAuth service apps use private_key_jwt for Okta API service access
- what the public/private key pair does
- what Okta stores and what your automation stores
- how the client assertion differs from the access token
- the required private_key_jwt assertion fields
- why the assertion audience must be the exact Org AS token endpoint
- why a new assertion should be created for each token request
- how the service app's Okta API scope grants work
- why scopes are necessary but not sufficient
- why the service app also needs admin role and resource authorization
- how read scopes differ from manage scopes
- why a token can contain a scope that the app still cannot successfully use for an operation
- how to automate read-only user and group calls safely
- how to perform a controlled group-membership write with least privilege
- how to rotate signing keys without putting private keys in source control
- how to distinguish client-authentication failure, scope-grant failure, and Management API authorization failure

[Open the Day 12 flow diagrams](../diagrams/day-12-okta-api-automation.md)

## Start with the requirement

Our new requirement is:

> A backend automation process needs to list Okta users and groups without using a human administrator's session or a long-lived SSWS API token.

The desired path is:

~~~text
Automation
    |
    | Client Credentials
    | private_key_jwt
    v
Okta Org Authorization Server
    |
    | scoped OAuth access token
    v
Okta Management API
~~~

There is no human user in this transaction.

## Why Day 12 is not Day 11 with another scope

Day 11:

~~~text
Protected resource:
Employee API

Authorization server:
Employee API Custom Authorization Server

Scope:
employee.report.read

Client authentication:
client_secret_basic

Authorization:
Custom-AS access policy + API scope check
~~~

Day 12:

~~~text
Protected resource:
Okta Management APIs

Authorization server:
Okta Org Authorization Server

Scopes:
okta.users.read
okta.groups.read
and other okta.* scopes as needed

Client authentication:
private_key_jwt

Authorization:
service-app scope grants
+
admin roles/resource access
~~~

Both use Client Credentials.

The surrounding security model is different.

## Why the Org Authorization Server

Okta API scopes belong to the Okta organization itself.

Examples:

~~~text
okta.users.read
okta.users.manage
okta.groups.read
okta.groups.manage
okta.apps.read
okta.logs.read
~~~

Only the Org Authorization Server mints access tokens containing Okta API scopes.

For an org:

~~~text
Issuer:
https://YOUR-OKTA-DOMAIN

Token endpoint:
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Do not use:

~~~text
/oauth2/default/v1/token
~~~

or:

~~~text
/oauth2/<custom-auth-server-id>/v1/token
~~~

for this service-app Okta Management API pattern.

## Org Authorization Server access tokens are for Okta

The access token returned in Day 12 is consumed by Okta.

Do not build your automation by decoding that access token and trusting its internal payload.

Treat it as opaque application data.

Use safe token-response metadata such as:

~~~text
token_type
expires_in
scope
~~~

and prove authorization by calling the actual Okta API.

This is different from Day 8 through Day 11, where our own API locally validated Custom Authorization Server JWTs.

## The API Services app

Create:

~~~text
Application type:
API Services

Name:
Okta Management Automation
~~~

This application represents the automation process.

It is not:

~~~text
a human administrator
a browser session
a SPA
an OIDC login app
~~~

It is a service principal in Okta's administrative authorization model.

## Why private_key_jwt

For a custom OAuth service app that requests Okta API scopes from the Org Authorization Server, Okta requires:

~~~text
private_key_jwt
~~~

for client authentication.

Do not copy Day 11:

~~~text
client_secret_basic
~~~

into this token request.

The service proves possession of its private key by signing a short-lived JWT client assertion.

Okta verifies that assertion with the corresponding public key registered on the service app.

## Public key vs private key

The relationship is:

~~~text
Your automation
    |
    | keeps PRIVATE key
    | signs client assertion
    v

Okta service app
    |
    | stores PUBLIC key
    | verifies signature
    v
client authenticated
~~~

The private key should not be uploaded to GitHub or pasted into normal shared documentation.

Okta needs the public key.

Your automation needs the private key.

## Key generation for this course

Day 12 includes a Python helper that generates:

~~~text
RSA 2048 private key
public JWK
random kid
~~~

locally.

The repository now ignores:

~~~text
secrets/
*.pem
*.key
.env
~~~

The helper writes key material under a local ignored directory.

The private key never belongs in a commit.

## What is a JWK?

A JWK is a JSON representation of a cryptographic key.

The public JWK contains fields similar to:

~~~json
{
  "kty": "RSA",
  "kid": "day12-...",
  "use": "sig",
  "alg": "RS256",
  "n": "...",
  "e": "AQAB"
}
~~~

The important idea is not memorizing n and e.

Understand:

~~~text
kid
-> tells Okta which registered public key should verify the assertion

public key
-> verifies signature

private key
-> creates signature
~~~

## Configure Public key / Private key authentication

On the API Services app, configure the client authentication method as:

~~~text
Public key / Private key
~~~

Then register the public JWK generated by the Day 12 helper.

A practical Okta behavior matters here:

> Changing the client authentication method from client-secret authentication to public/private key authentication removes the old client-secret model from this service app.

Do not plan to use a client secret as the token-endpoint credential for this Okta API service pattern.

## DPoP is a separate option

Some service-app configurations expose:

~~~text
Require Demonstrating Proof of Possession (DPoP) header in token requests
~~~

The core Day 12 helper does not implement DPoP.

For this lab, keep that requirement disabled.

Do not confuse the two key uses:

~~~text
private_key_jwt key pair
-> authenticates the OAuth client

DPoP key pair
-> sender-constrains a token/proves possession for DPoP requests
~~~

Okta documents these as separate JWKs.

Know the DPoP setting exists because an unexpected DPoP requirement can make an otherwise correct private_key_jwt token request fail.

DPoP stays a recognize-only advanced topic in this course.

## The client assertion

The client assertion is a short-lived JWT used to authenticate the OAuth client to the token endpoint.

It is not the Okta Management API access token.

~~~text
Client assertion
    |
    | proves service identity to /token
    v
Org Authorization Server
    |
    | returns
    v
Access token
    |
    | authorizes Okta API request
    v
/api/v1/users
~~~

## Client assertion header

For our RSA lab:

~~~json
{
  "alg": "RS256",
  "kid": "registered-key-id",
  "typ": "JWT"
}
~~~

The kid must identify the registered public key that matches the private key used to sign.

## Client assertion payload

The important claims are:

~~~text
iss = service app client ID
sub = service app client ID
aud = exact Org AS token endpoint
exp = short future expiration
iat = current time
jti = unique assertion identifier
~~~

For our org:

~~~text
aud =
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Not:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

Not:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default/v1/token
~~~

Not:

~~~text
https://YOUR-OKTA-DOMAIN/api/v1/users
~~~

The assertion authenticates the client to the token endpoint.

## iss and sub

Both are:

~~~text
service app client ID
~~~

Conceptually:

~~~text
iss
-> who created this client-authentication assertion

sub
-> which OAuth client identity this assertion represents
~~~

For this client-authentication method, they are the same client ID.

## Assertion expiration

Okta allows the assertion exp to be at most one hour in the future.

For engineering practice, create much shorter assertions.

Our helper uses a short lifetime.

A client assertion should be disposable.

Do not generate one assertion Monday morning and reuse it all week.

## jti

The jti is a unique identifier for the assertion.

The helper creates a fresh random jti for each token request.

When jti is supplied, the same assertion cannot be reused successfully.

Treat the client assertion as a one-time authentication proof.

## Token request

After signing the assertion, the automation sends:

~~~http
POST https://YOUR-OKTA-DOMAIN/oauth2/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
scope=okta.users.read okta.groups.read
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
client_assertion=<signed-client-assertion>
~~~

No client secret.

No browser.

No /authorize call.

No redirect URI.

No PKCE.

No ID token.

## The service app grants collection

Before the Org Authorization Server issues a requested Okta API scope, that scope must be granted to the service app.

In the app:

~~~text
Okta API Scopes
~~~

grant only what the automation needs.

For the read-only Day 12 path:

~~~text
okta.users.read
okta.groups.read
~~~

The Org Authorization Server checks the requested scopes against the service app's grants collection.

If the app was not granted a requested scope, token acquisition fails.

## Scope naming

Okta Management API scopes commonly follow:

~~~text
okta.<resource>.read
okta.<resource>.manage
~~~

Examples:

~~~text
okta.users.read
okta.users.manage
okta.groups.read
okta.groups.manage
okta.apps.read
okta.apps.manage
~~~

A manage scope generally includes the corresponding read capability for that API resource family.

Do not request manage when read is enough.

## Scopes are not the whole authorization model

This is one of the most important Okta implementation details in the course.

For Okta Management APIs:

~~~text
OAuth scope grant
+
admin role/resource authorization
=
actual capability
~~~

The scope answers:

> Is this OAuth client allowed to request an access token for this API resource/action family?

The admin role answers:

> Is this service principal administratively permitted to perform this operation on this resource?

Both matter.

## Scope issuance does not prove admin permission

Okta can issue a token containing a scope if that scope is in the app's grants collection.

That does not prove the service app's admin role permits every operation covered by the scope.

Example:

~~~text
Service app granted:
okta.groups.manage

Token request:
okta.groups.manage

Token request:
success

But service app admin role:
does not permit managing target group

Management API call:
denied
~~~

This is the Day 12 equivalent of:

~~~text
token successfully obtained
does not mean
every protected operation is authorized
~~~

## Primary lab role: Read-only Administrator

For the main lab, assign the service app:

~~~text
Read-only Administrator
~~~

and grant only:

~~~text
okta.users.read
okta.groups.read
~~~

Then the automation can practice:

~~~text
GET /api/v1/users
GET /api/v1/users/{id}
GET /api/v1/groups
~~~

without beginning with write access.

This is a safer first implementation and still demonstrates the complete service-app authorization model.

## Admin roles belong to the service app

Do not assign an admin role to a human user and assume that role transfers to the service app.

The OAuth service app is its own principal.

It needs its own administrative authorization.

## Public client app admins setting

Some Okta orgs have a setting that can automatically assign Super Administrator to service apps after scopes are granted.

Do not use that as the Day 12 design.

The course uses explicit role assignment and least privilege.

If that setting is enabled in a lab org, understand its effect before interpreting the service app's permissions.



## Optional controlled write exercise

After the read-only path is fully understood, the lab adds an optional controlled write test.

Create a dedicated group:

~~~text
OAuth-Day12-Test-Group
~~~

Then configure a narrow administrative assignment that permits the service app to manage membership for that test group.

Grant only the required OAuth scope for the operation.

For the lab operation:

~~~text
PUT /api/v1/groups/{groupId}/users/{userId}
~~~

the service needs the appropriate Okta API scope and sufficient administrative permission for that group.

The lab adds a test user, proves the result, removes the user, and restores the test group.

Do not use a production group for this exercise.

## The assertion and access token have different lifetimes

Client assertion:

~~~text
short lived
created per token request
used for client authentication
~~~

Access token:

~~~text
returned by Org Authorization Server
used as Bearer token for Okta Management API
fixed service-app access-token lifetime
~~~

Do not cache the assertion as if it were the access token.

## Access-token lifetime

Okta documents the OAuth service-app Org AS access token lifetime as fixed at one hour.

Your automation can cache that access token until shortly before expiry.

When it needs another:

~~~text
create fresh client assertion
        |
        v
POST /oauth2/v1/token
        |
        v
receive new access token
~~~

Do not reuse an expired assertion.

## Access-token caching

A normal automation pattern is:

~~~text
Need Okta API call
        |
        v
Cached access token exists?
        |
        +-- no -> build assertion and get token
        |
        +-- yes
              |
              v
near expiry?
        |
        +-- yes -> build NEW assertion and get token
        |
        +-- no -> reuse access token
~~~

The client assertion is generated only when a token request is needed.

## Treat the Org AS access token as opaque

The Day 12 helper will not decode the Okta API access token.

It records only:

~~~text
token_type
expires_in
scope response
~~~

Then it proves the token works by making an actual Okta API request.

That is intentional.

## Read users

With:

~~~text
okta.users.read
+
Read-only Administrator
~~~

the automation calls:

~~~http
GET https://YOUR-OKTA-DOMAIN/api/v1/users
Authorization: Bearer <access_token>
~~~

Record:

~~~text
HTTP status
number of returned records in the page
request ID or correlation headers when available
~~~

Do not dump user profiles into ordinary logs.

## Read one test user

Use a known lab user.

Call:

~~~text
GET /api/v1/users/{id-or-login}
~~~

This proves targeted reads separately from broad list calls.

Record only the small set of user fields you actually need for the exercise.

## Read groups

Grant:

~~~text
okta.groups.read
~~~

and call:

~~~text
GET /api/v1/groups
~~~

The pattern is:

~~~text
scope grant
+
admin role
+
Bearer access token
+
supported endpoint
~~~

## Three separate authorization layers

Day 12 failures must be classified into three layers.

### Layer 1: client authentication

Can Okta verify:

~~~text
client ID
kid
registered public key
signature
aud
exp
iss
sub
jti / replay
~~~

Failure here means:

~~~text
no access token
~~~

### Layer 2: scope grant

Did the service app receive permission to request:

~~~text
okta.users.read
okta.groups.read
and other required okta.* scopes
~~~

Failure here also means:

~~~text
no access token for that requested scope
~~~

### Layer 3: admin authorization

A token can be issued successfully.

Then the Management API can still deny the operation because the service app lacks:

~~~text
required admin role
resource target
custom-role permission
resource-set access
~~~

This is a post-token authorization failure.

Do not rebuild the client assertion when Layer 3 is the problem.

## Break/fix: wrong private key

Use a different private key from the one whose public key is registered for the kid.

Expected layer:

~~~text
client authentication
~~~

No Management API call should occur.

## Break/fix: wrong kid

Sign with the correct private key but place an unregistered kid in the JWT header.

Expected:

~~~text
Okta cannot select the matching registered verification key
-> client authentication fails
~~~

## Break/fix: wrong aud

Use:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default/v1/token
~~~

inside the assertion while posting to:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Expected:

~~~text
client assertion rejected
~~~

The aud identifies the resource the assertion authenticates to.

## Break/fix: expired assertion

Build:

~~~text
exp < current time
~~~

Expected:

~~~text
client authentication fails
~~~

The access token does not exist yet.

## Break/fix: replay assertion

Use the exact same assertion again when it contains the same jti.

Expected:

~~~text
replay protection rejects the reused assertion
~~~

Production automation should create a fresh assertion for each token request.

## Break/fix: scope not granted

Request:

~~~text
okta.apps.read
~~~

without granting that scope to the service app.

Expected:

~~~text
token acquisition fails
~~~

This is not an admin-role problem because the scope is not in the app's grants collection.

## Break/fix: scope granted but admin role removed

Keep:

~~~text
okta.users.read
~~~

granted to the service app.

Temporarily remove the admin role that gives the service principal permission to read the relevant users.

Request the token again.

Okta can still issue the granted scope.

Then call:

~~~text
GET /api/v1/users
~~~

Expected:

~~~text
Management API authorization failure
~~~

This proves:

~~~text
scope present
!=
administrative permission
~~~

Restore the admin role after the test.

## Break/fix: wrong resource target

This is easiest to see in the optional targeted group-membership exercise.

The service app can have:

~~~text
appropriate OAuth scope
+
admin role
~~~

but still be limited to:

~~~text
OAuth-Day12-Test-Group
~~~

A write to another group should fail if that group is outside the assigned administrative target.

This is the value of resource-scoped admin authorization.

## Standard role vs custom role

You should understand both.

### Standard role

Examples:

~~~text
Read-only Administrator
Group Membership Administrator
User Administrator
Application Administrator
~~~

These are quicker to configure.

Permissions are predefined.

Some standard roles support resource targets.

### Custom admin role

You define:

~~~text
specific permissions
~~~

and bind the role to:

~~~text
specific resource sets
~~~

Then the client app principal is included in the role/resource-set binding.

Custom roles are useful when a standard role is broader than the automation requirement.

You do not need to become a custom-role specialist today.

You do need to understand where custom roles fit into least privilege.

## Key rotation

A production service should not depend forever on one signing key.

A safe rotation pattern is:

~~~text
Current key A registered in Okta
        |
        v
Generate key B
        |
        v
Register public key B
        |
        v
Deploy private key B to automation
        |
        v
Automation signs with kid B
        |
        v
Verify successful token acquisition
        |
        v
Deactivate and retire public key A after safe overlap
~~~

Do not remove key A before every running instance of the automation has moved to key B.

When using Okta's signing-key management API, deactivate an old key before deleting it.

## Private-key storage

The private key should live in infrastructure designed for secrets or keys.

Examples:

~~~text
secret manager
key vault
protected filesystem with strict permissions
HSM or KMS-backed signing when supported
CI/CD secret store
~~~

Not:

~~~text
Git repository
shared ticket
wiki page
chat message
source-code constant
~~~

## Do not log the client assertion

The assertion is short lived, but it is still an authentication credential while valid.

Normal logs should contain:

~~~text
operation
client ID
kid
requested scope names
HTTP status
safe request/correlation identifiers
~~~

Not:

~~~text
private key
full client assertion
full access token
~~~

## Failure classification: invalid_client or token request rejected

Check:

~~~text
Org AS token endpoint?
private_key_jwt configured?
correct client ID?
correct private key?
kid registered?
iss = client ID?
sub = client ID?
aud = exact token endpoint?
exp valid?
jti replay?
clock reasonable?
~~~

## Failure classification: requested scope rejected

Check:

~~~text
scope name correct?
scope supported for Okta API?
scope granted on service app?
requesting only granted scopes?
~~~

## Failure classification: token succeeds but Okta API denies operation

Check:

~~~text
service app admin role?
role has required permission?
resource target includes this object?
custom role/resource-set binding correct?
endpoint supports that OAuth scope?
read vs manage scope appropriate?
~~~

Do not rotate keys first.

Client authentication already succeeded.

## Read vs manage

For GET-only automation:

~~~text
okta.users.read
okta.groups.read
~~~

is the right direction.

For create, update, or delete operations:

~~~text
okta.<resource>.manage
~~~

is normally required.

A manage scope includes read access for that resource family, so do not request read and manage redundantly without a reason.

## Day 12 evidence sources

The usual troubleshooting evidence changes slightly.

Use:

~~~text
automation HTTP response from /oauth2/v1/token
safe assertion metadata
token response scope and expires_in
Okta Management API HTTP response
Okta request/correlation identifiers
Okta System Log where applicable
service app scope grants
service app Admin Roles configuration
~~~

Do not rely on Browser Network.

There is no browser transaction.

## Common mistakes

### Mistake 1: Use a Custom Authorization Server

Wrong resource boundary.

Okta API scopes come from the Org Authorization Server.

### Mistake 2: Use client_secret_basic

Wrong service-app authentication model for custom OAuth access to Okta API scopes.

Use private_key_jwt.

### Mistake 3: Put the private key in source control

Wrong key handling.

Register the public key with Okta and protect the private key.

### Mistake 4: Set assertion aud to the Okta API endpoint

Wrong.

The assertion authenticates to the token endpoint.

### Mistake 5: Use the Custom-AS token endpoint in aud

Wrong.

Use:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

### Mistake 6: Assume the scope string proves admin permission

Wrong.

Scope grant and administrative authorization are separate.

### Mistake 7: Give the service app Super Admin for convenience

Poor implementation practice.

Start with least privilege.

### Mistake 8: Decode the Org AS access token and make authorization decisions from its payload

Wrong consumer.

Treat it as opaque and use it with Okta.

### Mistake 9: Reuse one client assertion indefinitely

Wrong credential lifecycle.

Build a fresh short-lived assertion for each token request.

### Mistake 10: Store the private key casually

Use protected key storage and strict access controls.

### Mistake 11: Troubleshoot an API authorization failure by changing kid

Wrong layer.

If the token was issued, client authentication already succeeded.

### Mistake 12: Grant manage scopes for read-only automation

Poor least privilege.

Grant only what the process needs.

## What you should be able to explain

1. Why does Day 12 use the Org Authorization Server?
2. Why is a Custom Authorization Server wrong for Okta API scopes?
3. What does private_key_jwt authenticate?
4. Which key stays with the automation?
5. Which key is registered with Okta?
6. What is kid used for?
7. Why are iss and sub both the client ID?
8. What must aud be?
9. Why should the assertion be short lived?
10. Why is jti useful?
11. What is the client assertion used for?
12. What is the access token used for?
13. Why should the Org AS access token be treated as opaque?
14. What are Okta API scope grants?
15. Why are scopes not enough?
16. What does an admin role add?
17. What do resource targets and resource sets add?
18. Why can token acquisition succeed but the API call fail?
19. When should you use read vs manage scopes?
20. How do you rotate signing keys safely?
21. How is Day 12 different from Day 11?

## Day 12 lab

[Day 12 Lab - Automate Okta Management APIs](../labs/day-12-okta-api-automation.md)

You will:

- generate a local RSA signing key pair
- keep private key material out of Git
- create an API Services app
- configure Public key / Private key client authentication
- register the public JWK
- grant okta.users.read and okta.groups.read
- assign a read-only admin role to the service app
- create a signed private_key_jwt client assertion
- obtain an Org AS access token
- call List Users
- read one test user
- call List Groups
- treat the Org AS access token as opaque
- deliberately use the wrong private key
- deliberately use the wrong kid
- deliberately use the wrong assertion aud
- deliberately use an expired assertion
- deliberately replay an assertion
- request an ungranted scope
- prove scope grant without admin permission is insufficient
- optionally perform a targeted test-group membership write
- practice a safe signing-key rotation
- classify every failure by layer

## Day 12 completion standard

Day 12 is complete when you can draw and explain:

~~~text
Automation
    |
    | create short-lived JWT assertion
    | iss = client_id
    | sub = client_id
    | aud = https://org/oauth2/v1/token
    | kid = registered public key
    | sign with private key
    v
Org Authorization Server /oauth2/v1/token
    |
    | validate private_key_jwt
    | requested scope granted to app?
    v
Okta API access token
    |
    | Bearer token
    v
Okta Management API
    |
    | required OAuth scope?
    | service app admin permission?
    | target resource allowed?
    v
operation
~~~

You should be able to diagnose:

~~~text
wrong key
wrong kid
wrong aud
expired assertion
replayed assertion
scope not granted
wrong scope
token succeeds but API denied
missing admin role
wrong resource target
read vs manage mismatch
~~~

without confusing those layers.

## Official references

- [Okta: Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
- [Okta: Set up Okta for OAuth API access](https://developer.okta.com/docs/guides/set-up-oauth-api/main/)
- [Okta: Client authentication methods](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth/)
- [Okta: OAuth 2.0 scopes](https://developer.okta.com/docs/api/oauth2)
- [Okta: Roles in Okta](https://developer.okta.com/docs/api/openapi/okta-management/guides/roles)
