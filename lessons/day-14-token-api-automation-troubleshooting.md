# Day 14 - Token, API, Refresh, and Automation Troubleshooting

## Goal for today

Day 13 trained browser and authentication troubleshooting.

Day 14 moves downstream.

The browser may already be out of the picture.

Today you troubleshoot:

~~~text
/token
access tokens
JWT validation
JWKS
API 401
API 403
refresh tokens
Client Credentials
Okta Management API automation
environment-specific token/API failures
~~~

There are no major new OAuth flows today.

The skill is classification.

By the end of Day 14, you should be able to take an incident such as:

> The API call is failing.

and determine whether the first failed layer is:

~~~text
client authentication
grant validation
scope/policy at token issuance
token trust
API authorization
refresh lifecycle
machine-client authorization
Okta administrative authorization
environment configuration
~~~

[Open the Day 14 troubleshooting diagrams](../diagrams/day-14-token-api-automation-troubleshooting.md)

## The Day 14 rule

Ask:

> Was a token issued?

That first split removes a large amount of guesswork.

~~~text
Token request
    |
    +-- no token
    |      |
    |      v
    |   troubleshoot /token
    |
    +-- token issued
           |
           v
       call resource
           |
           +-- 401
           |     |
           |     v
           |   token trust / validation
           |
           +-- 403
           |     |
           |     v
           |   permission / resource authorization
           |
           +-- success
                 |
                 v
              next application layer
~~~

## Evidence before interpretation

Capture safe evidence such as:

~~~text
grant type
authorization server issuer
token endpoint
client ID
client authentication method
requested scope names
HTTP status
OAuth error
OAuth error_description
token issued yes/no
token_type
expires_in
safe JWT header fields
safe JWT claims from Custom-AS token
API status
WWW-Authenticate
API correlation ID
API validation stage
Okta request ID
System Log event when relevant
~~~

Do not put these in shared tickets or logs:

~~~text
authorization code
PKCE verifier
client secret
private key
full client assertion
access token
refresh token
ID token
session cookie
~~~

## Start at the exact failing HTTP exchange

A user flow can be traced as:

~~~text
1. /authorize
2. callback
3. /token
4. resource API
5. refresh /token
6. later resource API
~~~

A machine flow can be traced as:

~~~text
1. client authentication
2. /token
3. resource API
~~~

Okta API automation can be traced as:

~~~text
1. private_key_jwt assertion
2. Org AS /token
3. Okta Management API
~~~

Name the step.

Do not say only:

> OAuth is failing.

## Token endpoint errors are pre-resource failures

If /token returns an OAuth error, then a usable access token was not issued.

The protected API is not the first failed layer.

Do not begin by changing:

~~~text
API audience validator
API CORS
API scope middleware
resource-server JWKS cache
~~~

when the client never obtained a token.

## Case 1: invalid_client

Interpretation:

> The authorization server could not accept the client authentication.

Investigate the authentication method configured for that client.

For client-secret clients:

~~~text
correct client ID?
correct secret?
secret rotated?
client_secret_basic vs client_secret_post?
Authorization header encoded correctly?
wrong environment secret?
~~~

For public clients:

~~~text
is client authentication supposed to be none?
did someone configure a confidential app type?
is a secret incorrectly being required?
~~~

For private_key_jwt:

~~~text
correct client ID?
private key matches registered public key?
kid registered?
iss = client ID?
sub = client ID?
aud = exact token endpoint?
exp valid?
jti replay?
correct Org AS token endpoint?
~~~

Do not investigate user MFA for a machine-client invalid_client error.

## Client ID vs client authentication credential

Keep these separate.

~~~text
client ID
-> identifier

client secret/private key proof
-> authentication credential
~~~

A correct client ID does not prove the client authenticated successfully.

## Case 2: invalid_grant

Do not memorize:

~~~text
invalid_grant = bad authorization code
~~~

The meaning depends on the grant being processed.

Ask first:

> Which grant_type was sent?

### Authorization Code

Possible branches include:

~~~text
authorization code expired?
code already redeemed?
wrong PKCE verifier?
redirect_uri differs from authorization request?
code belongs to another client/transaction?
wrong authorization server/token endpoint?
~~~

A code is short-lived and one-time.

Do not retry the same failed code indefinitely.

After correcting the cause, start a fresh authorization transaction.

### Refresh Token

Possible branches include:

~~~text
refresh token revoked?
refresh token expired?
wrong client?
wrong authorization server?
rotation changed the current token?
old rotating refresh token reused?
reuse detection invalidated token family?
~~~

The same OAuth error can point to a different credential depending on the grant.

## Authorization-code retry behavior

Suppose:

~~~text
code redeemed once
        |
        v
application loses token response
        |
        v
application submits same code again
~~~

The second exchange should fail.

The fix is not:

~~~text
retry same code ten times
~~~

The client needs a new authorization transaction.

## PKCE failure is a grant failure, not client-secret failure

For a SPA:

~~~text
client authentication = none
~~~

but token exchange can still fail because:

~~~text
code_verifier
~~~

does not match the challenge from the authorization request.

Do not call every /token failure client-authentication failure.

## Case 3: invalid_scope or scope request rejection

Ask these in order:

~~~text
Which authorization server?
Does the scope exist there?
Is the spelling exact?
Is the client requesting it?
Does an applicable access policy/rule permit it?
Does policy priority cause another rule to win?
Is the grant type allowed?
Does the user/no-user condition match?
~~~

For an Okta API service app ask:

~~~text
Is this an Okta API scope?
Is it granted to this service app?
Is the request going to the Org Authorization Server?
~~~

A scope can exist and still not be issuable to this client.

## Scope creation does not grant scope usage

For our Employee API:

~~~text
employee.report.read exists
~~~

does not mean:

~~~text
every OAuth client may receive employee.report.read
~~~

Policy still matters.

For Okta API automation:

~~~text
okta.apps.read exists
~~~

does not mean:

~~~text
this service app has been granted okta.apps.read
~~~

Keep existence and client authorization separate.

## Scope request rejected vs API insufficient scope

These happen at different times.

### Token endpoint

~~~text
Client requests salary.read
        |
        v
authorization server refuses request
        |
        v
no usable token
~~~

### Resource server

~~~text
Client has a valid token
        |
        v
token lacks salary.read
        |
        v
API accepts token
        |
        v
403 insufficient_scope
~~~

Do not use the same diagnosis for both.

## Case 4: API 401

For our bearer-token APIs, 401 means the request did not establish an acceptable bearer credential.

Work the validation pipeline:

~~~text
Authorization header present?
Bearer scheme correct?
token structurally parseable?
expected token type?
alg allowed?
kid present?
matching key in trusted JWKS?
signature valid?
issuer correct?
audience correct?
time claims valid?
expected client boundary correct?
required claims structurally valid?
~~~

Our course APIs log safe stages such as:

~~~text
bearer_token
jwt_header
algorithm
kid
jwks_key_resolution
signature
issuer
audience
expiration
client_id
scope_claim
~~~

Use the stage.

## Do not jump from 401 to scope

If the API says:

~~~text
401 invalid_token
stage=audience
~~~

do not start adding:

~~~text
employee.read
salary.read
~~~

The API has not trusted the token yet.

Scope authorization occurs after validation.

## Wrong token type

Common failures include sending:

~~~text
ID token
~~~

to an API, sending:

~~~text
Org Authorization Server access token
~~~

to your custom Employee API, or sending an Employee API token to an unrelated resource.

A token existing does not make it appropriate for every resource.

Ask:

> Who is the intended token consumer?

## Wrong issuer

The API starts from its configured trust boundary:

~~~text
expected issuer
~~~

Discovery then provides:

~~~text
jwks_uri
~~~

Do not let an incoming untrusted token choose a new issuer that the API automatically trusts.

If the token says issuer A but the API trusts issuer B, reject it.

## Wrong audience

Issuer answers:

> Which authorization server issued this credential?

Audience answers:

> Which resource was this credential intended for?

A token can have a valid signature, correct issuer, and valid lifetime and still be invalid for your API because the audience is wrong.

That is a token-trust failure.

## Case 5: API 403

If the token has already passed validation, move to authorization.

For our Employee API:

~~~text
required endpoint scope?
token scp?
claim/role rule if the API uses one?
requested resource?
authorization code path correct?
~~~

Example:

~~~text
trusted token
scp = [employee.read]

GET /api/salary
requires salary.read
        |
        v
403
~~~

Do not rotate signing keys.

The API already trusted the token.

## 401 vs 403 working rule

For this course:

~~~text
401
-> acceptable bearer authentication not established

403
-> bearer credential accepted but operation not permitted
~~~

This distinction is reflected in the course APIs through WWW-Authenticate.

A 403 is not a stronger 401.

It is a different decision.

## Case 6: unknown kid

A JWT header contains kid.

The validator uses it to find the public signing key in the JWKS from the trusted issuer.

If the kid is not in the API cached JWKS:

~~~text
1. confirm expected issuer
2. confirm discovery metadata
3. confirm jwks_uri
4. refresh JWKS from that trusted URI
5. check whether kid now exists
~~~

Okta rotates signing keys and publishes keys through the authorization server JWKS endpoint.

A validator should cache keys appropriately and refresh when necessary.

Do not permanently hardcode one signing key.

Do not disable signature validation.

## Unknown kid is not always rotation

Possible causes:

~~~text
legitimate key rotation and stale cache
wrong authorization server
token from another environment
token from another issuer
malformed/fabricated token
incorrect JWKS URL
application pinned to stale key material
~~~

Refresh the trusted JWKS once, then continue from evidence.

If the kid is still absent, rotation is not proven.

## Cache behavior matters

Production validators should:

~~~text
cache JWKS
respect caching guidance
refresh periodically
refresh on unknown kid when appropriate
avoid a network call for every API request
~~~

The trusted issuer remains the root of the lookup.

## Case 7: expired token

Compare:

~~~text
current system time
exp
configured validation leeway
clock synchronization
~~~

Do not extend token lifetime merely because an application failed to renew on time.

The correct fix may be:

~~~text
refresh before expiry
obtain another Client Credentials token
fix service token cache
fix local clock
~~~

depending on the architecture.

## Clock problems

Time validation can fail when:

~~~text
API clock is wrong
client assertion clock is wrong
container/VM clock is wrong
timezone display confuses operator
~~~

JWT time claims are numeric timestamps.

The issue is clock synchronization, not display timezone.

Do not add huge validation leeway to hide a broken clock.


## Case 8: refresh fails

First identify:

~~~text
Which refresh token is the client actually holding?
~~~

Then ask:

~~~text
Refresh Token grant enabled?
offline_access requested on the original authorization request when required?
correct client?
correct authorization server?
refresh token revoked?
refresh token expired?
rotation enabled?
client stored newly returned refresh token?
old token reused?
grace period relevant?
reuse detection event in System Log?
~~~

Okta rotates refresh tokens for SPAs by default and supports reuse detection.

A reused refresh token can invalidate newer tokens in the authorization family.

## Do not test refresh reuse carelessly

A live rotating refresh token is a credential.

Repeatedly replaying an old token can invalidate:

~~~text
latest refresh token
access tokens issued since authentication
~~~

Use a disposable lab authorization if you explicitly test reuse.

For the core Day 14 lab, use the controlled Day 10 revocation flow and inspect reuse-detection concepts without risking a useful token family.

## Refresh failure after access-token revocation

Remember Day 10:

~~~text
revoke access token only
        |
        +-- access token inactive at Okta
        |
        +-- refresh token remains active
~~~

Therefore:

~~~text
refresh succeeds after access-token-only revocation
~~~

can be expected.

Do not classify it as a revocation failure.

## Refresh failure after refresh-token revocation

Also from Day 10:

~~~text
revoke refresh token
        |
        v
refresh token inactive
        |
        v
associated access token inactive at Okta
        |
        v
later refresh fails
~~~

The failed credential is the refresh token.

Name it.

## Case 9: locally valid JWT but revoked at Okta

This is not necessarily a contradiction.

A locally validated Custom-AS JWT can still have:

~~~text
valid signature
correct issuer
correct audience
exp in the future
required scope
~~~

after the authorization server has marked it inactive.

Therefore:

~~~text
local API = 200
/introspect = active:false
~~~

can occur.

The API is answering:

> Does this JWT satisfy my local trust rules?

Introspection is answering:

> Does the authorization server currently consider this token active?

Different evidence.

## Case 10: Client Credentials token request fails

For Day 11 service access, classify in this order:

~~~text
correct Custom Authorization Server?
correct service client ID?
client_secret_basic configured?
secret correct?
Client Credentials grant allowed?
policy assigned to this client?
policy priority correct?
User = No user?
service scope exists?
scope permitted?
~~~

Browser concepts such as redirect URI, cookies, state, nonce, and CORS are not the first layer.

There is no interactive browser transaction.

## Case 11: service token issued but machine API returns 401

Now /token is proven successful.

Check Day 11 resource-server trust:

~~~text
issuer
audience
signature
expiry
expected service cid
scp structure
~~~

If:

~~~text
stage=client_id
~~~

the API may have validated the JWT signature/issuer/audience but rejected the configured client boundary.

Do not rotate the client secret.

That credential already succeeded at /token.

## Case 12: service token issued but machine API returns 403

If the token is trusted and:

~~~text
employee.report.read
~~~

is missing from scp, the machine endpoint returns insufficient scope.

Investigate:

~~~text
what scope did the service request?
what scope did the authorization server grant?
what scope does the endpoint require?
~~~

Do not troubleshoot MFA or user groups.

There is no human user in the Day 11 transaction.

## Case 13: Okta API private_key_jwt token request fails

This is Day 12 Layer 1.

Check:

~~~text
Org Authorization Server /oauth2/v1/token?
private_key_jwt configured?
correct client ID?
private key matches registered public key?
kid registered?
iss = client ID?
sub = client ID?
aud = exact Org-AS token endpoint?
iat/exp valid?
jti reused?
DPoP requirement unexpectedly enabled?
~~~

No Okta Management API call should occur if client authentication fails.

## Case 14: Okta API scope request fails

This is Day 12 Layer 2.

Check:

~~~text
scope supported?
scope spelling?
scope granted on service app?
read vs manage?
request sent to Org Authorization Server?
~~~

Do not assign Super Administrator to solve a scope that was never granted.

Administrative roles are evaluated later.

## Case 15: Okta API token issued but operation denied

This is the critical Day 12 distinction.

Proven:

~~~text
private_key_jwt succeeded
Org AS issued access token
requested scope was granted to service app
~~~

Now inspect:

~~~text
admin role assigned to service app?
role contains required permission?
resource target contains target object?
custom role/resource-set binding correct?
endpoint requires a manage scope instead of read?
~~~

A new client assertion does not repair missing admin permission.

## Okta API authorization has two independent controls

~~~text
OAuth scope grant
        +
admin role/resource authorization
        =
usable operation
~~~

You need both.

Do not flatten them into:

> The token has the scope, so Okta should allow it.

## Case 16: dev works, prod fails

Do not say:

> Same code, so it must be Okta.

The code can be identical while trust configuration differs.

Compare:

~~~text
authorization server issuer
authorization server ID
audience
client ID
client authentication method
secret/key/kid
redirect URI when user flow
scope definitions
scope grants
access policies
policy priority
grant type
user/no-user condition
admin roles
resource targets
JWKS
custom domain
API base URL
expected cid
token lifetime
refresh configuration
clock
network/proxy
~~~

Create a difference matrix.

## Dev/prod token comparison

For Custom-AS JWTs, safely compare:

~~~text
iss
aud
cid
scp
kid
iat
exp
~~~

Do not compare full token strings.

The tokens should be different.

You are comparing trust metadata.

## Environment-secret mismatch

Common failures include:

~~~text
prod client ID
+
dev client secret
~~~

or:

~~~text
prod client ID
+
dev private key
~~~

or:

~~~text
prod token
+
dev API expected audience
~~~

Those combinations are internally inconsistent.

Check related values as pairs, not one field in isolation.

## HTTP status alone is not enough

Example:

~~~text
401
~~~

does not tell you whether the stage was:

~~~text
missing bearer token
wrong audience
expired token
wrong cid
unknown kid
invalid signature
~~~

Use:

~~~text
WWW-Authenticate
API correlation ID
safe validation stage
~~~

when available.

Likewise:

~~~text
/token HTTP 400
~~~

is not enough.

Capture:

~~~text
error
error_description
grant_type
client authentication method
~~~

without logging credentials.

## System Log evidence on Day 14

System Log can help with:

~~~text
OAuth token events
refresh-token reuse detection
service-app events
administrative changes
policy/configuration events
~~~

But your custom API local validation stage remains application evidence.

A System Log event cannot replace:

~~~text
Employee API correlation log
~~~

when the failure happened inside your API.

## Troubleshooting order by layer

Use this sequence.

### Layer 1: Can the client reach the correct token endpoint?

~~~text
DNS/network/TLS
correct issuer
correct token endpoint
~~~

### Layer 2: Can the client authenticate?

~~~text
none
client_secret_basic
client_secret_post
private_key_jwt
~~~

### Layer 3: Is the grant acceptable?

~~~text
authorization code
PKCE
refresh token
Client Credentials
code/token validity
~~~

### Layer 4: Are requested scopes issuable?

~~~text
scope exists
policy/grant/user condition
client scope grant
~~~

### Layer 5: Was a token issued?

If no:

~~~text
stop before resource-API troubleshooting
~~~

### Layer 6: Does the resource trust the token?

~~~text
token type
alg
kid/JWKS
signature
iss
aud
time
cid
~~~

### Layer 7: Does the trusted token authorize the operation?

~~~text
scope
claim/role if designed
resource target
admin permission
~~~

### Layer 8: Does the application process success correctly?

~~~text
response parsing
cache
state
retry
business logic
~~~

Day 14 focuses mostly on Layers 1 through 7.

## Retry behavior

Not every failure should be retried.

### Usually configuration or credential failures

Examples:

~~~text
invalid_client
wrong audience
ungranted scope
wrong kid/private key
missing admin role
~~~

Do not retry forever.

Alert and correct configuration.

### Potentially transient failures

Examples:

~~~text
network timeout
temporary 5xx
rate limiting
~~~

Use bounded retry and backoff appropriate to the API.

Do not turn every HTTP error into the same retry loop.

## Token acquisition success should be logged safely

Useful:

~~~text
token_endpoint_status=200
grant_type=client_credentials
client_id=...
scope=employee.report.read
expires_in=900
~~~

Unsafe:

~~~text
access_token=eyJ...
client_secret=...
refresh_token=...
~~~

Troubleshooting does not require credential leakage.

## API validation success should be logged safely

Useful:

~~~text
correlation_id=...
result=allowed
issuer=expected
audience=expected
client_id=expected
required_scope=employee.report.read
~~~

Avoid dumping the full JWT.

## Root cause vs symptom

Symptom:

> The API says 401.

Root cause:

> Production API expected audience api://employee-service-prod, but the client presented a token from the dev authorization server with audience api://employee-service-dev.

Symptom:

> Refresh stopped working.

Root cause:

> The SPA continued using an older rotating refresh token instead of the current token returned by the authorization server.

Symptom:

> Okta Users API returns an authorization error.

Root cause:

> The service app successfully received okta.users.read, but the administrative role required to read users was removed.

The root cause names the broken relationship.

## Incident-note format

For every Day 14 case write:

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

This format is deliberately similar to Day 13.

The protocol stage is different.

## Common mistakes

### Mistake 1: Debug API scope before a token exists

Wrong layer.

Fix /token first.

### Mistake 2: Treat every token endpoint error as invalid_client

Wrong.

Grant and scope errors are separate.

### Mistake 3: Treat invalid_grant as one root cause

Wrong.

Identify the grant type and credential.

### Mistake 4: Add scopes to fix wrong audience

Wrong.

The token is not trusted by that resource.

### Mistake 5: Interpret every denial as 401

Wrong.

Trusted credential with insufficient permission is normally 403 in our APIs.

### Mistake 6: Disable signature validation for unknown kid

Never.

Refresh the trusted JWKS and verify issuer/configuration.

### Mistake 7: Hardcode one signing key forever

Wrong.

Signing keys rotate.

### Mistake 8: Increase token lifetime to hide refresh bugs

Wrong operational fix.

Repair renewal behavior.

### Mistake 9: Replay rotating refresh tokens casually

Risky.

Reuse detection can invalidate the authorization family.

### Mistake 10: Debug browser CORS for Client Credentials

Wrong transaction.

### Mistake 11: Rotate private_key_jwt keys when the Okta API token was already issued

Wrong layer.

Investigate Management API authorization.

### Mistake 12: Assign Super Admin because one Okta API call is denied

Overprivileged workaround.

Find the required scope, role, permission, and resource target.

### Mistake 13: Compare dev and prod only by source code

Incomplete.

OAuth trust configuration is part of the system.

### Mistake 14: Log credentials to make troubleshooting easier

Never.

Log safe metadata and correlation identifiers.

## What you should be able to explain

1. What is the first Day 14 question?
2. Why does no token mean the API is not the first failed layer?
3. What does invalid_client point you toward?
4. Why does invalid_grant require knowing the grant type?
5. How can PKCE cause token exchange failure without a client-secret problem?
6. What is the difference between scope existence and scope authorization?
7. What is the difference between token-endpoint scope rejection and API 403?
8. What does 401 mean in the course resource servers?
9. What does 403 mean?
10. Why can a signed token still fail audience validation?
11. How should unknown kid be investigated?
12. Why is disabling signature validation never the fix?
13. What should happen when an access token expires?
14. Why should huge clock leeway not hide time-sync problems?
15. What should you inspect when refresh fails?
16. Why is refresh-token replay a dangerous casual lab test?
17. Why can local JWT validation disagree with introspection?
18. What should you check for a Day 11 Client Credentials failure?
19. Why is a Day 11 API 401 different from invalid_client at /token?
20. What are the three Day 12 failure layers?
21. Why can an Okta API token contain a scope while the operation is denied?
22. How do you compare dev and prod safely?
23. Which failures should not be retried forever?
24. What evidence belongs in a useful incident note?

## Day 14 lab

[Day 14 Lab - Token, API, Refresh, and Automation Troubleshooting](../labs/day-14-token-api-automation-troubleshooting.md)

The lab reuses the working systems from Days 8 through 12 and adds one safe local token probe.

You will diagnose failures without changing unrelated layers.

## Day 14 completion standard

Day 14 is complete when you can take:

> API access is broken.

and ask, in order:

~~~text
Was a token issued?
        |
        +-- no
        |    |
        |    v
        | client auth?
        | grant?
        | scope/policy?
        |
        +-- yes
             |
             v
        Did resource trust token?
             |
             +-- no -> 401 validation path
             |
             +-- yes
                  |
                  v
             Was operation allowed?
                  |
                  +-- no -> 403 / permission path
                  |
                  +-- yes -> next application layer
~~~

For refresh:

~~~text
Which refresh token?
Which client?
Which issuer?
Revoked/expired?
Rotated?
Latest token stored?
Reuse detected?
~~~

For Okta API automation:

~~~text
private_key_jwt
        |
        v
scope grant
        |
        v
admin/resource authorization
~~~

You must be able to identify the first failed layer without random configuration changes.

## Official references

- [Okta: Client authentication methods](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth)
- [Okta: Validate access tokens](https://developer.okta.com/docs/guides/validate-access-tokens/main/)
- [Okta: Key rotation](https://developer.okta.com/docs/concepts/key-rotation/)
- [Okta: Refresh access tokens and rotate refresh tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Okta: Protect your API endpoints](https://developer.okta.com/docs/guides/protect-your-api/main/)
- [Okta: Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
