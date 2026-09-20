# The 15-day execution plan

The 15 days are **modules, not deadlines**.

Do not move to the next day because a clock or calendar says to move on. Move on when you can explain the current topic, complete its evidence-based lab, and meet the completion standard in the lesson.

The course deliberately starts with architecture and HTTP before touching real OAuth configuration.

## Day 1 - Core logic and architecture

Learn:

- authentication vs API authorization
- OAuth vs OIDC
- client, authorization server, resource server, protected resource
- ID token vs access token consumers
- public vs confidential clients
- user-facing vs machine clients
- where OAuth/OIDC stops and provisioning begins

Do:

- classify application components
- draw the user path
- draw the no-user service path
- explain who consumes each token

Do not configure Okta yet.

Completion target:

- you can look at a requirement and identify the main trust relationships without discussing protocol parameters

## Day 2 - HTTP and transaction tracing

Learn:

- HTTP request and response
- methods, URLs, paths, query parameters
- headers and form bodies
- 200, 302, 400, 401, 403
- redirects
- front channel vs back channel
- cookies
- bearer Authorization header
- browser behavior vs Postman

Do:

- run the local Day 2 HTTP server
- inspect requests in Browser DevTools
- follow a 302 redirect
- observe a cookie
- send a form POST
- compare missing, wrong, and correct demo bearer credentials

Do not configure Okta or troubleshoot a real OAuth callback yet.

Completion target:

- you can read the HTTP transaction that OAuth/OIDC will use on later days

## Day 3 - Authorization Code + PKCE

Learn deeply:

- authorization request
- authorization code
- callback
- state
- nonce
- code_verifier
- code_challenge
- S256
- code exchange
- public-client behavior
- PKCE vs client authentication

Do:

- create a real Okta SPA integration
- manually inspect the Authorization Code + PKCE transaction using the browser, callback receiver, and Postman

Break/fix:

- wrong verifier
- reused code
- wrong redirect URI

Completion target:

- you can draw the full flow and explain why every major value exists

## Day 4 - ID, access, and refresh tokens

Learn:

- ID token consumer
- access token consumer
- refresh token consumer
- expiration
- offline_access
- refresh-token sensitivity
- refresh-token rotation
- why an Org Authorization Server access token is not your custom API token

Do:

- inspect real token responses
- decode an ID token for inspection
- obtain a refresh token
- refresh the token set

Break/fix:

- missing offline_access
- invalid refresh token

Completion target:

- you can explain the lifecycle and consumer of each token without mixing them

## Day 5 - JWT validation, discovery, and JWKS

Learn:

- JWT header, payload, signature
- alg and kid
- trusted issuer
- discovery
- jwks_uri
- signature validation
- issuer, audience, expiration, issued-at, nonce
- key rotation
- decode vs validate
- validation vs authorization

Do:

- validate a real Okta ID token using a standard library
- tamper with a token and prove validation fails

Break/fix:

- wrong issuer
- wrong audience
- wrong nonce
- expired token
- unknown kid
- modified signature

Completion target:

- you can explain what cryptographic validation proves and what it does not prove

## Day 6 - Okta app types and client authentication

Learn:

- SPA, Web Application, Native, API Services
- architecture before app type
- none
- client_secret_basic
- client_secret_post
- client_secret_jwt
- private_key_jwt
- redirect and sign-out URIs
- grant types
- assignments and Controlled Access
- client authentication vs PKCE

Do:

- compare a public SPA and a confidential Web Application
- inspect their different token-endpoint authentication behavior

Break/fix:

- invalid_client
- wrong app type/client-authentication expectation
- assignment/access mismatch

Completion target:

- you can choose the app type and client-authentication method from the actual runtime architecture

## Day 7 - Server-side Web Application vs browser SPA

Implement and compare:

- server-side Web Application
- browser SPA using Authorization Code + PKCE

Understand:

- who is the OAuth client
- who calls /token
- where state, nonce, verifier, secret, and tokens live
- local application session
- browser-accessible token storage and XSS exposure
- Backend for Frontend as an architectural option
- CORS and Trusted Origins as different browser/configuration concerns

Completion target:

- you can explain the trust-boundary difference between a server-side Web Application and a SPA

## Day 8 - Protect the Employee API

Learn and implement:

- Custom Authorization Server tokens for an API you own
- API audience
- employee.read
- local JWT validation
- validation before authorization
- 401 vs 403
- WWW-Authenticate
- safe correlation logging

Prove:

~~~text
no or invalid token
-> 401

valid token without employee.read
-> 403

valid token with employee.read
-> 200
~~~

Completion target:

- you can protect a resource server without using an ID token or Org-AS token as the API credential

## Day 9 - Authorization-server design

Learn deeply:

- Org vs Custom Authorization Server
- dedicated API audience
- custom scopes
- requested vs permitted vs granted
- explicit default-scope exception
- groups as eligibility conditions
- claims as information
- access-policy allowlists
- first-match rule order
- token lifetime by rule
- Token Preview
- authentication policy vs Authorization Server Access Policy

Build:

- dedicated Employee API Authorization Server
- employee.read
- salary.read
- HR eligibility group
- custom claims
- HR-specific salary rule
- normal employee rule

Prove:

- HR membership does not inject an unrequested scope
- non-HR salary request is denied
- rule ordering changes the outcome

Completion target:

- scopes, claims, groups, audience, and policy no longer feel interchangeable

## Day 10 - Sessions and token lifecycle

Learn and prove:

- Okta browser session
- local application session
- ID token
- access token
- refresh token
- UserInfo
- refresh rotation
- local logout vs Okta logout
- revocation
- introspection
- local JWT validation vs current authorization-server state

Break/fix:

- immediate SSO after local logout
- revoked access token with refresh still active
- revoked refresh token
- claim differences by requested scopes

Completion target:

- you can predict which state changes after each lifecycle action

## Day 11 - Client Credentials and machine-to-machine

Implement:

- API Services client for the Employee API
- client_secret_basic
- Client Credentials
- employee.report.read
- no-user access-policy rule
- machine-token caching
- protected machine endpoint

Break/fix:

- wrong client credential
- unknown/disallowed scope
- wrong expected service client ID
- trusted token missing required service scope

Completion target:

- you can troubleshoot a no-user flow without bringing browser/MFA concepts into it

## Day 12 - Okta Management API automation

Implement:

- API Services app for Okta Management APIs
- local RSA key pair
- private_key_jwt
- Org Authorization Server
- Okta API scope grants
- service-app admin role/resource authorization
- read-only Management API calls
- optional narrow write
- safe key rotation

Break/fix:

- wrong key
- wrong kid
- wrong assertion audience
- expired assertion
- assertion replay
- ungranted scope
- scope granted but admin permission missing

Completion target:

- you can keep client authentication, OAuth scope grant, and Okta administrative authorization as three separate layers

## Day 13 - Browser and authentication troubleshooting

No new major OAuth feature.

Diagnose blind cases using:

- Browser Network
- Console/storage/cookies
- application stage logs
- Okta System Log
- last-successful-step reasoning

Cases include:

- redirect mismatch
- lost transaction
- state mismatch
- nonce mismatch
- local-session failure
- wrong issuer
- Controlled Access/assignment
- unexpected MFA
- local vs Okta logout
- CORS/preflight
- Trusted Origins
- Postman works/browser fails
- dev works/prod fails

Completion target:

- you can turn "login failed" into a specific failed transaction stage with evidence

## Day 14 - Token, API, refresh, and automation troubleshooting

Diagnose:

- invalid_client
- invalid_grant by grant type
- scope rejection
- malformed/invalid bearer token
- 401 vs 403
- wrong issuer/audience
- unknown kid/JWKS refresh
- signature failure
- expiry/clock problems
- refresh revocation/rotation issues
- Client Credentials failures
- Okta API private_key_jwt failures
- Okta API scope grant vs admin-role/resource failure
- environment drift
- retry vs alert behavior

Completion target:

- you can classify a downstream incident by token endpoint, token trust, resource authorization, refresh lifecycle, or administrative authorization

## Day 15 - End-to-end implementation capstone

You receive a mixed requirement containing:

- React employee portal
- Java API
- employee access
- HR-only salary access
- scheduled no-user reporting
- refresh
- logout
- dev/prod
- future Okta Management automation
- least privilege and safe logging

First produce:

- missing questions
- explicit assumptions
- architecture
- trust-boundary table
- client/resource classification
- authorization-server design
- scope/claim/policy design
- refresh/logout behavior
- machine design
- environment matrix
- observability plan

Then prove the OAuth/OIDC security contract using either:

1. React + Spring Boot when that stack is comfortable to you, or
2. the course SPA/API harnesses for protocol proof, followed by mapping the same design to the supplied React + Spring Boot reference.

Finally:

- complete the acceptance matrix
- diagnose at least twelve blind failures from different layers
- restore temporary break/fix changes
- produce the project and operations handoff
- explain the same architecture to an application owner, developer, and IAM/security engineer

Completion target:

- you can receive an unfamiliar OAuth/OIDC project or incident and reason from the trust relationships and evidence rather than memorized steps
