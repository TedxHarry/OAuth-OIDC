# Day 11 - Client Credentials and Machine-to-Machine OAuth

## Goal for today

Days 3 through 10 focused mainly on OAuth flows involving a human user.

Day 11 removes the human completely.

The requirement is:

> Every night, an Employee Reporting Service needs to call the Employee API and retrieve reporting data. No person is sitting at a browser.

This is machine-to-machine OAuth.

By the end of Day 11, you should understand:

- when Client Credentials is appropriate
- why there is no user in this flow
- why there is no browser
- why there is no authorization endpoint redirect
- why there is no Authorization Code
- why there is no PKCE transaction
- why there is no ID token
- why there is normally no refresh-token lifecycle
- what an API Services app represents
- what client authentication proves
- why a service client must be confidential
- why the service needs a custom API scope
- why OpenID scopes are wrong in Client Credentials
- why the access-policy rule must use No user
- why a policy must explicitly allow the Client Credentials grant
- why the service scope still has to be enforced by the API
- how to cache and renew service access tokens
- how to distinguish invalid_client from invalid_scope and API 403
- why Day 11 and Day 12 use different authorization-server/client-authentication designs

[Open the Day 11 flow diagrams](../diagrams/day-11-client-credentials.md)

## Start with the real requirement

Assume this process runs every night:

~~~text
Employee Reporting Service
        |
        | retrieve employee reporting data
        v
Employee API
~~~

There is:

~~~text
no employee at a browser
no login screen
no Okta browser session
no interactive consent
~~~

The service itself needs permission.

That changes the OAuth architecture.

## User-delegated flow vs machine flow

Earlier:

~~~text
Employee
   |
   v
SPA
   |
   | Authorization Code + PKCE
   v
Okta
   |
   | access token representing user-authorized request
   v
Employee API
~~~

Day 11:

~~~text
Reporting Service
   |
   | authenticates as OAuth client
   v
Okta /token
   |
   | access token
   v
Reporting Service
   |
   | Bearer access token
   v
Employee API
~~~

The service is not pretending to be a user.

That is the core Client Credentials idea.

## What is intentionally absent

A correct Client Credentials flow does not require:

~~~text
browser
/authorize redirect
user login
Okta browser session
state
nonce
authorization code
PKCE verifier
PKCE challenge
ID token
UserInfo
~~~

Those objects solve problems that belong to interactive user flows.

Do not add them because they appeared in earlier lessons.

## Why there is no ID token

An ID token answers a user-authentication question for an OIDC client.

Client Credentials has:

~~~text
no end user
~~~

Therefore:

~~~text
ID token
-> not part of this flow
~~~

The service receives an OAuth access token.

## Why OpenID scopes are wrong here

Okta documents that Client Credentials has no user context and therefore cannot request OpenID scopes.

Do not request:

~~~text
openid
profile
email
offline_access
~~~

for the Day 11 service.

Create and request a custom API scope instead.

Our scope will be:

~~~text
employee.report.read
~~~

Interpret it as:

> Permission for an authorized service client to read the reporting endpoint of the Employee API.

## Why we reuse the Employee API Authorization Server

Day 9 created:

~~~text
Employee API Authorization Server

Audience:
api://employee-service
~~~

That authorization server represents the Employee API product.

The new scheduled service calls the same API product.

Therefore we do not need a second authorization server merely because the caller is a machine.

We add another client and another permission model to the same API security boundary.

~~~text
Employee Portal SPA
        |
        | user scopes
        v
Employee API Authorization Server
        |
        v
Employee API


Employee Reporting Service
        |
        | service scope
        v
Employee API Authorization Server
        |
        v
Employee API
~~~

One API product can have both user-delegated and machine callers.

## Create a service-specific scope

Day 11 adds:

~~~text
employee.report.read
~~~

Why not reuse:

~~~text
employee.read
~~~

We could design that deliberately, but the course uses a separate service scope so the authorization boundary is obvious.

Now the API can distinguish:

~~~text
employee.read
-> user-facing employee endpoint

salary.read
-> HR user salary endpoint

employee.report.read
-> machine reporting endpoint
~~~

This demonstrates least-privilege scope design.

## API Services application

In Okta, create an application integration using:

~~~text
Sign-in method:
API Services
~~~

The application represents:

~~~text
Employee Reporting Service
~~~

It is a confidential OAuth client.

Okta provides:

~~~text
Client ID
Client secret
~~~

for the service app.

The client secret is a credential.

Treat it like a password.

## Why this client can use a secret

A scheduled server process can keep credentials away from end users.

Conceptually:

~~~text
server environment
secret manager
vault
protected deployment configuration
~~~

This is different from a SPA.

A browser SPA cannot safely keep a long-lived client secret because the user controls the browser environment.

## Client authentication vs API authorization

Keep two decisions separate.

### Decision 1: authenticate the OAuth client

At /token:

~~~text
Client ID + client secret
        |
        v
Okta verifies service client
~~~

Question:

> Is this really the registered Employee Reporting Service client?

### Decision 2: authorize API operation

At the Employee API:

~~~text
valid access token
        |
        v
employee.report.read present?
~~~

Question:

> Does this trusted token grant the reporting operation?

Client authentication does not automatically grant every API permission.

## Client Credentials token request

The service makes one direct back-channel request:

~~~http
POST <token_endpoint>
Authorization: Basic <base64(client_id:client_secret)>
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&scope=employee.report.read
~~~

There is no browser redirect.

There is no /authorize request first.

There is no callback.

## client_secret_basic

For our Day 11 custom-API service app, use:

~~~text
client_secret_basic
~~~

Conceptually:

~~~text
client_id:client_secret
        |
        v
Base64 encode
        |
        v
Authorization: Basic ...
~~~

The secret is not the bearer access token.

The secret authenticates the client to the token endpoint.

The access token is the credential later presented to the resource server.

## Do not manually publish the Basic value

For the lab, Python requests or Postman Basic Auth can build the header for you.

Do not paste:

~~~text
client_id:client_secret
~~~

into shared notes.

Do not commit the Base64 value either.

Base64 encoding is not encryption.

## Custom scope and user consent

Client Credentials has no user who can click a consent screen.

Therefore service scopes must be configured so they can be used by a service flow.

If a scope is configured to require user consent in a way that blocks services, a Client Credentials request cannot satisfy that requirement.

For:

~~~text
employee.report.read
~~~

use a service-compatible consent configuration.

The lab uses implicit/no interactive user consent for this training scope.

## Access policy for the service client

The Employee API Authorization Server already contains user-oriented policies from Day 9.

Do not put the service into the SPA policy and hope an existing rule matches.

Create a separate policy:

~~~text
Employee Reporting Service Access
~~~

Assign it only to:

~~~text
Employee Reporting Service
~~~

That makes the client boundary explicit.

Policy priority still matters.

Okta evaluates matching policies and rules in priority order and stops at the first match. If your authorization server contains an earlier broad policy such as:

~~~text
All clients
~~~

that policy can intercept the service request before the dedicated reporting policy is reached.

For the lab, confirm there is no earlier broad policy that matches the Employee Reporting Service.

## The service rule must say No user

This is one of the most important Okta-specific Day 11 details.

A Client Credentials request has no user.

Therefore its access-policy rule must contain a condition that applies to:

~~~text
No user
~~~

A rule requiring:

~~~text
Any user assigned the app
~~~

cannot correctly represent this Client Credentials transaction.

Our rule is:

~~~text
Name:
Reporting Service Client Credentials

Grant type:
Client Credentials

User:
No user

Custom scope:
employee.report.read

Access token lifetime:
15 minutes
~~~

This is a different policy path from the SPA rules.

## Why no user condition matters

Compare:

~~~text
Authorization Code

user authenticates
        |
        v
policy can evaluate user/group
~~~

with:

~~~text
Client Credentials

service authenticates
        |
        v
there is no user/group identity
        |
        v
rule must allow No user
~~~

Do not troubleshoot a service token request by checking whether an employee is assigned to the application.

There is no employee in the transaction.

## Policy evaluation still matters

Client Credentials is simple, but it is not:

~~~text
correct secret
-> automatically receive any scope
~~~

The authorization server still evaluates:

~~~text
Which client?
Which grant type?
No-user condition?
Which custom scope was requested?
Which policy and rule match?
~~~

Only then can the token be issued.

## Requested, permitted, granted still applies

Day 9 taught:

~~~text
requested
-> permitted
-> granted
~~~

That model still applies.

For the reporting service:

~~~text
Service requests:
employee.report.read
        |
        v
Service policy covers this client
        |
        v
Client Credentials rule matches
        |
        v
No user condition matches
        |
        v
employee.report.read allowed
        |
        v
access token scp includes employee.report.read
~~~

Same authorization principle, different actor.

## Expected token response

A successful Client Credentials request returns an access token response similar to:

~~~json
{
  "access_token": "<access-token>",
  "token_type": "Bearer",
  "expires_in": 900,
  "scope": "employee.report.read"
}
~~~

Exact lifetime depends on your rule.

Do not expect:

~~~text
authorization code
ID token
refresh token
~~~

in this flow.

## Why no refresh token pattern

Client Credentials already assumes the service can authenticate itself again.

When the access token is near expiration:

~~~text
service
   |
   | client credentials again
   v
/token
   |
   v
new access token
~~~

That is normally simpler than carrying a user-style refresh-token lifecycle into a machine identity.

## Service token identity

Do not interpret a Client Credentials token as:

> User Harish logged in.

There is no user in the flow.

Okta access-token claims differ when there is no user bound to the token. For example, user-specific claims such as uid are not present when no user is bound.

The most important Day 11 identity fact for our API is:

~~~text
cid
-> OAuth client that obtained the token
~~~

and:

~~~text
scp
-> permissions granted to that client token
~~~

The API must still validate issuer, audience, time, and the expected client boundary.

## Extend the Employee API safely

Day 11 adds:

~~~text
GET /api/service-report
~~~

Required scope:

~~~text
employee.report.read
~~~

The API will validate the token exactly as before.

Then it checks:

~~~text
employee.report.read in scp?
~~~

If yes:

~~~text
200
~~~

If not:

~~~text
403
~~~

## Keep user and service endpoints understandable

Our training API now has:

~~~text
/api/employees
requires employee.read

/api/salary
requires salary.read

/api/service-report
requires employee.report.read
~~~

The scope names make the intended caller/operation clear.

That is easier to review than:

~~~text
api.full_access
~~~

## Machine identity is not human identity

Avoid code like:

~~~text
if token has no employee username:
    authentication failed
~~~

A Client Credentials token is expected to have no end-user identity.

The API should validate what this flow is supposed to contain.

The service caller is identified by the OAuth client relationship, not by inventing a user.

## Token caching

A scheduled process should not request a new token for every API call if an existing token is still safely reusable.

A normal pattern:

~~~text
Need API access
        |
        v
Cached access token exists?
        |
        +-- no -> get token
        |
        +-- yes
              |
              v
near expiration?
        |
        +-- yes -> get new token
        |
        +-- no -> reuse token
~~~

This reduces unnecessary token traffic.

## Do not use an expired token until the API rejects it

The service should understand the token lifetime returned by the authorization server.

A simple implementation can store:

~~~text
access_token
expires_in
acquired_at
~~~

and renew a little before expiration.

Do not create an outage window by waiting until after expiry when the service already knows the lifetime.

## Do not retry invalid credentials forever

Consider:

~~~text
wrong client secret
        |
        v
/token fails
        |
        v
service retries every second forever
~~~

That is poor operational behavior.

A better service:

~~~text
token acquisition fails
        |
        v
classify failure
        |
        +-- transient network/server issue
        |      -> bounded retry/backoff
        |
        +-- invalid client/configuration
               -> fail and alert
~~~

Authentication configuration errors need correction, not infinite retry.

## Secret storage and rotation are part of the design

For every service client ask:

~~~text
Where is the secret stored?
Who can read it?
How is it injected into the process?
How is it rotated?
Can old and new credentials overlap during rotation?
What alert occurs when token acquisition fails?
What is the scope blast radius if the secret is stolen?
~~~

OAuth design is not finished when the first token request succeeds.

## Least privilege

The service should request only:

~~~text
employee.report.read
~~~

for this job.

Do not request:

~~~text
salary.read
employee.read
every available scope
~~~

unless the service genuinely needs them and the policy intentionally permits them.

Both the client request and policy should be narrow.

## Scope denied at token issuance vs scope denied at API

These are different failures.

### Token issuance failure

~~~text
service requests salary.read
        |
        v
service policy does not allow salary.read
        |
        v
/token fails
~~~

The API is never called.

### API authorization failure

~~~text
service has valid token
but
token lacks required endpoint scope
        |
        v
API returns 403
~~~

Both are authorization failures, but they occur at different layers.

## invalid_client

If:

~~~text
client ID wrong
client secret wrong
client authentication method wrong
~~~

the token endpoint can reject the client.

Think:

~~~text
Could Okta authenticate the OAuth client?
~~~

Do not troubleshoot API audience first when the service never obtained a token.

## invalid_scope or policy rejection

If:

~~~text
client authenticated
but
requested scope is unknown or not permitted
~~~

the failure belongs to the authorization request/policy layer.

Check:

~~~text
correct Custom Authorization Server
scope exists
service-compatible consent
policy covers client
Client Credentials grant allowed
No user rule
scope permitted by rule
~~~

## 401 from the Employee API

If the service obtained a token but the API returns 401:

~~~text
token missing?
wrong token?
wrong authorization server?
wrong audience?
expired?
signature/JWKS issue?
unexpected cid?
~~~

This is token acceptance.

## 403 from the Employee API

If the API returns 403:

~~~text
token was accepted
but
required endpoint scope is missing
~~~

Check:

~~~text
Which scope does endpoint require?
Which scopes are in token scp?
Did service request the right scope?
~~~

Do not change client secret when the API already trusted the token.

## No browser means browser troubleshooting is irrelevant

For Client Credentials:

~~~text
redirect URI
CORS
browser cookies
Okta SSO session
state
nonce
PKCE
callback routing
~~~

are not part of the token transaction.

If a scheduled service fails at 2 AM, opening browser DevTools is not the first evidence source.

Use:

~~~text
service logs
HTTP token response
safe token claims
API response
API logs
Okta System Log when relevant
~~~

## Day 11 vs Day 12

Both use service applications and Client Credentials.

They protect different resources.

### Day 11

~~~text
Resource:
Our Employee API

Authorization server:
Employee API Custom Authorization Server

Scope:
employee.report.read

Client authentication in our lab:
client_secret_basic

Authorization:
Custom-AS policy + API scope enforcement
~~~

### Day 12

~~~text
Resource:
Okta Management APIs

Authorization server:
Okta Org Authorization Server

Scopes:
okta.* scopes

Client authentication:
private_key_jwt

Authorization:
Okta scopes + admin roles/resource assignments
~~~

Do not copy Day 11's client secret request into Day 12.

Do not copy Day 12's Okta API scope model into Day 11.

## Common mistakes

### Mistake 1: Add a user to Client Credentials

Wrong.

The service is acting as itself.

### Mistake 2: Request openid with Client Credentials

Wrong.

There is no OIDC user authentication context.

Use a custom API scope.

### Mistake 3: Expect an ID token

Wrong.

Client Credentials returns an access token for the resource.

### Mistake 4: Expect a user refresh-token lifecycle

Wrong pattern.

The confidential service can authenticate again to obtain another access token.

### Mistake 5: Reuse the SPA access-policy rule

Wrong.

The service rule needs Client Credentials and No user.

### Mistake 6: Put a user/group condition on the service rule

Wrong actor.

There is no user.

### Mistake 7: Treat the client secret as an API bearer token

Wrong credential purpose.

The secret authenticates the client to /token.

### Mistake 8: Put client secret in source control

Never.

Use protected runtime secret storage.

### Mistake 9: Request every scope because the service is trusted

Poor least privilege.

Trusted infrastructure still needs narrow authorization.

### Mistake 10: Assume successful client authentication grants all scopes

Wrong.

The access policy/rule still decides what can be issued.

### Mistake 11: Troubleshoot redirect URI or CORS

Wrong flow.

There is no browser redirect.

### Mistake 12: Use Day 11 client_secret_basic for Okta Management API automation

Wrong Day 12 model.

Okta Management API service access has a different authorization-server and client-authentication design.

## What you should be able to explain

1. When should Client Credentials be used?
2. Who is the actor in Client Credentials?
3. Why is there no browser?
4. Why is there no ID token?
5. Why should you not request openid?
6. Why does the service need a custom scope?
7. Why is API Services a confidential client?
8. What does client_secret_basic prove?
9. Why does the access policy still matter after client authentication succeeds?
10. Why must the rule use No user?
11. Why must Client Credentials be explicitly allowed as the grant type?
12. Why do we create employee.report.read rather than giving the service every user scope?
13. What does cid identify?
14. Why should the service cache a valid access token?
15. Why is infinite retry wrong for invalid_client?
16. What is the difference between token-endpoint scope denial and API 403?
17. Why are CORS and redirect URI irrelevant to this flow?
18. How is Day 11 different from Day 12?

## Day 11 lab

[Day 11 Lab - Machine-to-Machine Employee Reporting](../labs/day-11-client-credentials.md)

You will:

- create employee.report.read
- create an API Services app named Employee Reporting Service
- keep its client secret local
- create a client-specific Custom-AS access policy
- create a Client Credentials / No user rule
- obtain a real machine access token
- inspect the token safely
- prove there is no ID token or refresh token
- call a real machine-protected Employee API endpoint
- deliberately use a wrong client secret
- deliberately request an unknown scope
- deliberately break the No user rule
- deliberately remove Client Credentials from the rule
- deliberately request a user scope the service policy does not allow
- prove API 403 with the wrong valid scope
- implement token caching and renewal
- distinguish client authentication, token issuance authorization, and API authorization failures

## Day 11 completion standard

Day 11 is complete when you can draw:

~~~text
Employee Reporting Service
        |
        | client ID + secret
        | grant_type=client_credentials
        | scope=employee.report.read
        v
Employee API Authorization Server
        |
        | authenticate client
        | policy for this service?
        | grant = Client Credentials?
        | user = No user?
        | scope permitted?
        v
access token
        |
        | aud = api://employee-service
        | cid = service client
        | scp = employee.report.read
        v
Employee API
        |
        | validate token
        | require employee.report.read
        v
report data
~~~

You should be able to troubleshoot:

~~~text
invalid client
wrong authorization server
unknown scope
scope not permitted
wrong policy
wrong policy priority
wrong grant
wrong user condition
wrong audience
expired token
API 401
API 403
~~~

without inventing a human user or browser flow.

## Official references

- [Okta: Implement Client Credentials](https://developer.okta.com/docs/guides/implement-grant-type/clientcreds/main/)
- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: Create an authorization server](https://developer.okta.com/docs/guides/customize-authz-server/main/)
- [Okta: Configure an access policy](https://developer.okta.com/docs/guides/configure-access-policy/main/)
- [Okta: Protect your API endpoints](https://developer.okta.com/docs/guides/protect-your-api/main/)
