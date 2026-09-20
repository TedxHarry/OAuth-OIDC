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
