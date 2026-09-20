# Day 8 - Protect an API: Validate First, Authorize Second

## Goal for today

Days 3 through 7 focused mostly on the OAuth/OIDC client side.

Today you move to the resource-server side and protect a real endpoint:

~~~text
GET /api/employees
~~~

The API makes two separate decisions:

~~~text
Decision 1
Can I trust this access token?

Decision 2
Does this trusted token grant employee.read?
~~~

By the end of Day 8, you should understand:

- why an API receives an access token, not an ID token
- why the Org Authorization Server token from earlier days cannot protect your own API
- why your API needs a Custom Authorization Server token
- issuer, audience, cid, exp, and scp from the API perspective
- how the API validates a JWT access token
- why validation happens before scope authorization
- why missing or invalid credentials lead to 401
- why a valid token with insufficient scope leads to 403
- why frontend button visibility is not API security
- how to log useful diagnostics without leaking bearer tokens

[Open the Day 8 flow diagrams](../diagrams/day-08-protect-api.md)

## Start from the API perspective

A request arrives:

~~~http
GET /api/employees
Authorization: Bearer eyJ...
~~~

The API does not ask:

> Did this user previously see an Okta login page?

It asks:

~~~text
Bearer token present?
        |
        v
Can I trust the token?
        |
        v
Was it issued by the authorization server I trust?
        |
        v
Was it issued for this API audience?
        |
        v
Is it still valid?
        |
        v
Does it grant employee.read?
~~~

The API evaluates the credential presented on the current request.

A previous browser sign-in is not sufficient.

## Three separate concepts

### User authentication

Earlier in the course:

~~~text
Employee
   |
   v
Okta
   |
   v
user authentication succeeds
~~~

### Access-token validation

At the API:

~~~text
Bearer access token
        |
        v
Can the API trust this credential?
~~~

### API authorization

Only after the token is trusted:

~~~text
Trusted access token
        |
        v
employee.read present?
        |
        +-- yes -> allow
        |
        +-- no  -> deny
~~~

Working rule:

> Validate first. Authorize second.

## The API needs an access token

Recall Day 4:

~~~text
ID token
-> intended for the OIDC client

Access token
-> intended for a resource server
~~~

The Employee API is a resource server.

Correct:

~~~http
Authorization: Bearer <access_token>
~~~

Wrong:

~~~http
Authorization: Bearer <id_token>
~~~

An ID token that proves an authentication result to a client does not become an API authorization credential.

## Why the Org Authorization Server token is wrong

Days 3 through 7 used the Okta Org Authorization Server:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

Its access tokens are intended for Okta.

Do not build this:

~~~text
Org Authorization Server
        |
        | Okta access token
        v
Employee API
~~~

For an API that you own and validate yourself, use a Custom Authorization Server:

~~~text
Custom Authorization Server
        |
        | access token intended for your API
        v
Employee API
~~~

This is the first important architecture change in Day 8.

## Org server vs default Custom Authorization Server

The names are easy to confuse.

~~~text
Org Authorization Server

Issuer:
https://YOUR-OKTA-DOMAIN


Default Custom Authorization Server

Issuer:
https://YOUR-OKTA-DOMAIN/oauth2/default
~~~

They are different authorization servers.

For Day 8 we use the preconfigured Custom Authorization Server named:

~~~text
default
~~~

Day 9 teaches authorization-server design in depth.

## Check that Custom Authorization Servers are available

In the Admin Console:

~~~text
Security
  |
  v
API
  |
  v
Authorization Servers
~~~

If your org does not expose Authorization Servers, do not substitute an Org Authorization Server token and pretend the API is protected correctly.

Custom Authorization Servers are part of Okta API Access Management for production use. Testing-plan availability can vary.

The correct architecture matters more than forcing the lab to run in an incompatible tenant.

## Audience

An access token is not intended for every resource server.

The Custom Authorization Server has an Audience setting.

The default server is commonly configured with:

~~~text
api://default
~~~

but do not assume that value.

Open the default Custom Authorization Server and record the actual configured Audience.

The API will expect that value.

~~~text
Authorization Server Audience
        |
        v
access-token aud claim
        |
        v
API expected audience
~~~

If the token audience does not match the API expectation:

~~~text
reject
~~~

On Day 9 we replace the generic lab audience with a deliberate Employee API design.

## Create one API permission

Our endpoint is:

~~~text
GET /api/employees
~~~

For Day 8 it requires one custom scope:

~~~text
employee.read
~~~

Interpret it as:

> Permission to read the Employee API resource used in this lab.

The client requests employee.read.

The authorization server decides whether that scope can be granted.

If granted, Okta records it in the access token scp claim.

Example:

~~~json
{
  "scp": [
    "openid",
    "employee.read"
  ]
}
~~~

The API checks the granted scopes in the trusted token.

Do not authorize from what the client originally requested.

## Why an access policy is needed

Creating employee.read does not mean every client automatically receives it.

The Custom Authorization Server evaluates access policies and rules.

For today:

~~~text
Client requests token
        |
        v
Does a policy apply to this client?
        |
        v
Does a rule match the request?
        |
        v
Can the requested scopes be issued?
        |
        v
Token can be minted
~~~

A newly provisioned default Custom Authorization Server may not have a basic access policy.

If no matching policy and rule exist:

~~~text
token request fails
~~~

The lab therefore checks for a policy and creates the minimum training configuration if necessary.

Day 9 teaches policy order, rule conditions, scope restrictions, and token lifetimes properly.

## Why the Day 8 policy is intentionally broad

Our test matrix requires two valid tokens:

~~~text
Token A
valid token WITH employee.read

Token B
valid token WITHOUT employee.read
~~~

So the Day 8 policy allows the training SPA to request the scopes needed for both cases.

That is a teaching configuration.

It is not the final authorization model.

Day 9 tightens it.

## Important access-token claims

A Custom Authorization Server access token is a signed JWT.

Important claims include:

~~~text
iss
aud
sub
iat
exp
cid
scp
~~~

### iss

Expected issuer:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default
~~~

Question:

> Did the authorization server trusted by this API issue the token?

### aud

Expected value:

~~~text
the Audience configured for the default Custom Authorization Server
~~~

Question:

> Was this token issued for the resource audience this API accepts?

### exp

Question:

> Is the token still within its validity period?

Expired tokens are rejected.

### cid

Okta includes the OAuth client ID in:

~~~text
cid
~~~

Our Day 8 API accepts only the one SPA client used for this lab.

That makes the client boundary visible.

A later production design can deliberately support multiple allowed clients.

### scp

Okta records granted scopes in:

~~~text
scp
~~~

The API reads scp only after token validation has succeeded.

## Never authorize from an unvalidated JWT

Unsafe:

~~~text
decode token
        |
        v
see employee.read
        |
        v
allow request
~~~

Anyone can alter an unvalidated JWT payload.

Correct:

~~~text
validate signature and claims
        |
        v
trusted token
        |
        v
read scp
        |
        v
check employee.read
~~~

Day 5 taught the trust problem.

Day 8 applies it to access tokens.

## Access-token validation pipeline

Our API uses this sequence:

~~~text
Request arrives
        |
        v
Bearer token present?
        |
        v
JWT header acceptable?
        |
        v
Resolve signing key from trusted JWKS
        |
        v
Signature valid?
        |
        v
iss matches expected Custom AS?
        |
        v
aud matches expected API audience?
        |
        v
time claims valid?
        |
        v
cid matches allowed Day 8 client?
        |
        v
TOKEN TRUSTED
~~~

Then and only then:

~~~text
employee.read in scp?
        |
        +-- yes -> 200
        |
        +-- no  -> 403
~~~

## Discovery and JWKS

The API starts from its configured trusted issuer:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default
~~~

OIDC discovery:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/default/.well-known/openid-configuration
~~~

The API verifies that the discovered issuer matches the configured issuer.

It obtains jwks_uri from that trusted metadata.

Then:

~~~text
token kid
   |
   v
trusted JWKS
   |
   v
matching public key
   |
   v
signature verification
~~~

The token itself does not get to choose an arbitrary issuer that the API suddenly trusts.

## 401 vs 403

This distinction matters.

### 401 Unauthorized

For our bearer-token API, examples include:

~~~text
no bearer token
malformed token
invalid signature
wrong issuer
wrong audience
expired token
wrong cid for this lab
ID token sent instead of API access token
Org-AS access token sent to this custom API
~~~

The API could not establish an acceptable bearer credential.

### 403 Forbidden

403 is used when:

~~~text
credential accepted
but
required permission missing
~~~

Day 8 example:

~~~text
valid Custom-AS access token
        |
        v
employee.read missing
        |
        v
403 Forbidden
~~~

RFC 6750 defines the bearer-token distinction:

~~~text
invalid_token
-> normally 401

insufficient_scope
-> normally 403
~~~

## WWW-Authenticate

Bearer-protected APIs communicate authentication challenges through:

~~~text
WWW-Authenticate
~~~

### Missing token

~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="employee-api"
~~~

### Invalid token

~~~http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="employee-api", error="invalid_token"
~~~

### Valid token but missing employee.read

~~~http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer realm="employee-api", error="insufficient_scope", scope="employee.read"
~~~

Do not include the bearer token itself in an error response.

## Scope enforcement belongs on the API

Frontend logic can improve the user experience:

~~~text
if user cannot use employee.read:
    hide employee button
~~~

That is not security enforcement.

A caller can skip the UI and invoke the API directly.

Therefore:

~~~text
Frontend
-> may hide unavailable actions

Employee API
-> must enforce employee.read
~~~

The resource server owns its endpoint authorization.

## Scope vs claim

For this first API design:

~~~text
scope
-> API permission

claim
-> fact or context carried in the token
~~~

Possible scopes:

~~~text
employee.read
salary.read
expense.approve
~~~

Possible contextual claims:

~~~text
department
employeeType
groups
~~~

Day 8 uses one rule only:

~~~text
GET /api/employees
requires employee.read
~~~

Day 9 expands the design.

## The four core outcomes

### Case 1: no token

~~~text
No Authorization header
        |
        v
401
~~~

### Case 2: invalid token

Examples:

~~~text
garbage
ID token
wrong authorization server
wrong audience
~~~

Result:

~~~text
401
~~~

### Case 3: valid token, insufficient scope

~~~text
signature valid
issuer valid
audience valid
cid accepted
not expired
employee.read missing
        |
        v
403
~~~

### Case 4: valid token, correct scope

~~~text
token validation passes
employee.read present
        |
        v
200
~~~

The learner must run all four.

## Safe API diagnostics

Bearer tokens are credentials.

Bad log:

~~~text
token=eyJhbGciOi...
~~~

Good log:

~~~text
correlation_id=...
path=/api/employees
result=invalid_token
stage=audience_check
~~~

For missing permission:

~~~text
correlation_id=...
path=/api/employees
result=insufficient_scope
required_scope=employee.read
~~~

Our API never logs the raw bearer token.

## Correlation IDs

Each lab request receives a random correlation ID.

The API returns it in:

~~~http
X-Correlation-ID: ...
~~~

and logs the same ID.

That lets you connect:

~~~text
Postman response
        |
        v
API terminal log
~~~

without exposing credentials.

## Local validation is not live revocation checking

Day 8 validates JWTs locally using trusted signing keys and claims.

It does not ask Okta about the token on every request.

So Day 8 does not prove:

~~~text
this token has not been revoked right now
~~~

Revocation and introspection are different lifecycle topics.

Day 10 covers them.

## Common mistakes

### Mistake 1: Send the ID token to the API

Wrong.

The ID token is intended for the OIDC client.

### Mistake 2: Send an Org Authorization Server access token to your API

Wrong.

That access token is intended for Okta.

### Mistake 3: Decode the access token and trust employee.read

Wrong.

Validate first.

### Mistake 4: Check only the JWT signature

Incomplete.

Issuer, audience, time claims, and other required checks still matter.

### Mistake 5: Hide the UI button and call the endpoint protected

Wrong.

The API must enforce employee.read.

### Mistake 6: Return 403 for every token problem

That loses the distinction between invalid credentials and insufficient permission.

### Mistake 7: Return 401 when employee.read is missing from an otherwise valid token

The token is trusted. The permission is insufficient.

Use 403.

### Mistake 8: Log full bearer tokens

Wrong.

Log failure categories and correlation IDs.

### Mistake 9: Assume the default Custom Authorization Server already has an access policy

Check it.

Some new test orgs require you to create one.

### Mistake 10: Copy the broad Day 8 lab policy into production

Do not.

Day 9 designs the policy properly.

## What you should be able to explain

1. Why can the Employee API not use the Org Authorization Server access token?
2. Why does the API use a Custom Authorization Server?
3. What does audience mean to the resource server?
4. Where does Okta record employee.read in the access token?
5. What must be validated before the API trusts scp?
6. Why does an ID token fail as an API credential?
7. What produces 401 in this lab?
8. What produces 403?
9. Why must the API enforce scope even if the frontend hides an action?
10. Why does the API begin from a configured trusted issuer?
11. Why is local JWT validation different from live revocation checking?
12. What does a correlation ID help prove?

## Day 8 lab

[Day 8 Lab - Protect the Employee API](../labs/day-08-protect-api.md)

You will:

- inspect the default Custom Authorization Server
- record its issuer and actual audience
- create employee.read
- create the minimum lab access policy and rule when needed
- obtain a valid access token with employee.read
- validate it in a real Python API
- obtain a valid token without employee.read
- prove 403
- send no token and prove 401
- send garbage and prove 401
- send an ID token and prove 401
- configure the wrong audience and prove 401
- correlate each request with safe API logs

## Day 8 completion standard

Day 8 is complete when you can draw:

~~~text
Client
  |
  | asks Custom Authorization Server for employee.read
  v
Custom Authorization Server
  |
  | evaluates policy/rule
  | returns signed access token
  v
Client
  |
  | Authorization: Bearer access_token
  v
Employee API
  |
  | validate token
  v
trusted?
  |
  +-- no -> 401
  |
  +-- yes
       |
       | employee.read present?
       |
       +-- no -> 403
       |
       +-- yes -> 200
~~~

You must be able to say precisely:

> The token was rejected

or:

> The token was accepted, but the requested operation was denied

without mixing the two.

## Official references

- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: Create an authorization server](https://developer.okta.com/docs/guides/customize-authz-server/main/)
- [Okta: Protect your API endpoints](https://developer.okta.com/docs/guides/protect-your-api/main/)
- [Okta: API Access Management](https://developer.okta.com/docs/concepts/api-access-management/)
- [Okta: OAuth 2.0 and OpenID Connect access-token claims](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/overview)
- [RFC 6750: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html)
