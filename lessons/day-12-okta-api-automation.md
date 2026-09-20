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

