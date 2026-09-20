# Day 13 - Browser and Authentication Troubleshooting from Evidence

## Goal for today

Day 13 introduces no major OAuth or OIDC feature.

Today you practice operating the system you already built.

The most important question is:

> What is the last step I can prove succeeded?

Do not start by guessing:

~~~text
Okta problem
CORS problem
MFA problem
cookie problem
assignment problem
OAuth problem
~~~

First locate the transaction.

By the end of Day 13, you should be able to diagnose browser and sign-in incidents involving:

- wrong redirect URI
- wrong client ID or app type
- lost OAuth transaction state
- state mismatch
- nonce mismatch
- wrong issuer
- app assignment and Controlled Access
- unexpected MFA or reauthentication
- Global Session Policy vs app sign-in policy
- Okta browser session vs local application session
- login loops
- browser cookies and privacy behavior
- CORS
- Trusted Origins
- SPA callback processing
- Web Application callback processing
- works in Postman but fails in browser
- environment-specific browser failures
- evidence correlation in the Okta System Log

[Open the Day 13 troubleshooting diagrams](../diagrams/day-13-browser-auth-troubleshooting.md)

## The Day 13 rule

For every ticket, write:

~~~text
Observed symptom:

Last confirmed successful step:

First failed step:

Evidence:

Root cause:

Change:

Proof after change:
~~~

If you cannot name the last successful step, you are not ready to change configuration.

## A browser sign-in is a transaction, not one event

For a redirect-based OIDC flow, think in checkpoints:

~~~text
1. User opens application
        |
        v
2. Application creates OAuth transaction
        |
        v
3. Browser receives redirect to Okta
        |
        v
4. Browser reaches /authorize
        |
        v
5. Okta identifies/authenticates user
        |
        v
6. Okta evaluates sign-in policies/app access
        |
        v
7. Okta redirects to registered callback
        |
        v
8. Application receives code + state
        |
        v
9. Application validates transaction state
        |
        v
10. Client exchanges code at /token
        |
        v
11. Client validates OIDC response
        |
        v
12. Application creates local authenticated state
        |
        v
13. User reaches protected application page
~~~

A ticket saying Login failed does not tell you which checkpoint failed.

Your job is to find it.

## The three-source proof rule

Use three evidence sources when they apply.

### Source 1: browser or HTTP evidence

Examples:

~~~text
Browser Network
Browser Console
Browser Application / Storage
Postman
curl
backend HTTP logs
~~~

Question:

> What exact request or local browser/application step failed?

### Source 2: token or transaction evidence

Examples:

~~~text
issuer
audience
state returned
nonce expected
scope
token present yes/no
cookie present yes/no
transaction record present yes/no
~~~

Do not paste live tokens into tickets.

Question:

> What was actually issued or retained?

### Source 3: Okta System Log

Use it to inspect:

~~~text
user
application
time
outcome
policy evaluation
session behavior
authentication events
assignment-related events
transaction correlation
~~~

Useful correlation fields include:

~~~text
transaction.id
authenticationContext.externalSessionId
authenticationContext.rootSessionId
~~~

Do not expect System Log to tell you whether your Python application forgot to create its own local session.

That is application evidence.

## Start from the user-visible symptom, then move inward

Suppose the user says:

> I click Sign in and get an error.

Do not immediately open the authorization-server configuration.

Instead ask:

~~~text
Did the browser leave the application?
Did it reach Okta?
Was the user identified?
Was a factor requested?
Was /authorize accepted?
Did Okta send a callback?
Did the callback reach the app?
Did the app call /token?
Did the app create its own authenticated state?
~~~

Each answer removes entire categories of causes.

## Browser evidence setup

Before reproducing a browser incident:

~~~text
Open DevTools
Network
Preserve log = enabled
~~~

Inspect:

~~~text
URL
method
status
initiator
request headers
response headers
query parameters
form data
redirect chain
timing
~~~

Also inspect:

~~~text
Console
Application / Storage
Cookies
Session Storage
Local Storage
~~~

Do not copy:

~~~text
authorization code
access token
refresh token
ID token
session cookie value
PKCE verifier
client secret
~~~

into an incident note.

Capture presence, location, status, and safe metadata instead.

## Case 1: redirect URI mismatch

Typical location:

~~~text
Browser reached Okta /authorize
        |
        v
authorization request rejected
        |
        X
application callback not reached
~~~

Compare exactly:

~~~text
redirect_uri in actual /authorize request

vs

Sign-in redirect URI registered on the Okta app
~~~

Compare the whole string:

~~~text
scheme
hostname
port
path
environment
~~~

Examples:

~~~text
http://localhost:5000/callback
!=
http://localhost:5000/callback2
~~~

~~~text
https://app.example.com/callback
!=
https://app-test.example.com/callback
~~~

Do not diagnose callback bug until you prove which URI was sent and which URI was registered.

## Why the callback may never receive the error

Redirect URI validation is a security boundary.

If the requested redirect URI is not allowed, Okta cannot safely send authorization data to that untrusted URI.

Therefore:

~~~text
No callback request
~~~

can itself be evidence.

## Case 2: callback reached application but state validation fails

Now the failure is later.

Proven:

~~~text
/authorize accepted
user reached Okta
callback reached app
code/state returned
~~~

Failed:

~~~text
application transaction correlation
~~~

Investigate:

~~~text
expected state
returned state
pending transaction record
transaction cookie/storage
server restart
load balancer/session affinity
browser storage cleared
multiple simultaneous login attempts
wrong tab/window
application callback handler
~~~

Do not rotate the client secret.

The application has not yet proven that the callback belongs to the transaction it started.

## State mismatch vs missing transaction

These can look similar but are not identical.

### State mismatch

~~~text
expected state exists
returned state exists
values differ
~~~

### Missing transaction

~~~text
callback arrives
but
application no longer has expected state/verifier/nonce
~~~

Examples:

~~~text
server restarted
session store lost
transaction cookie blocked
browser storage cleared
callback handled by another node without shared state
~~~

State binds the browser response to the transaction the client started.

## Case 3: nonce validation fails

Nonce belongs later in the OIDC validation path.

~~~text
callback accepted
state validated
/token succeeded
ID token returned
        |
        v
nonce in ID token does not match expected nonce
        |
        X
OIDC response rejected
~~~

Proven:

~~~text
authorization request succeeded
code exchange succeeded
ID token was returned
~~~

Failed:

~~~text
OIDC response binding
~~~

Investigate:

~~~text
expected nonce storage
transaction mix-up
wrong token/transaction
multiple tabs
application state corruption
incorrect library usage
~~~

Do not call this an MFA failure.

## State and nonce answer different questions

~~~text
state
-> does this browser authorization response belong to my request?

nonce
-> does this ID token belong to the OIDC authentication request I started?
~~~

Do not treat them as interchangeable.

## Case 4: wrong issuer

Issuer errors can appear at different points depending on architecture.

### Issuer does not exist

The client can fail while loading:

~~~text
/.well-known/openid-configuration
~~~

before the browser authorization flow starts.

### Issuer is real but wrong

The flow can travel further.

Failures can appear in:

~~~text
endpoint selection
policy/scope behavior
ID-token issuer validation
access-token audience/issuer behavior
~~~

Always record the configured issuer exactly.

Then fetch discovery from that exact issuer and check:

~~~text
metadata issuer
authorization_endpoint
token_endpoint
jwks_uri
~~~

Do not guess endpoint paths.

## Case 5: app assignment and Controlled Access

Do not automatically say:

> The user is not assigned.

First inspect the app's access model.

If Controlled Access requires assignments, investigate:

~~~text
direct user assignment
group assignment
group membership
app status
user status
System Log outcome
~~~

If the app allows everyone in the organization, lack of an explicit individual assignment is not the same failure.

The app access model decides whether assignment is required.

## Assignment failure location

A useful distinction:

~~~text
Browser reached Okta
user identified/authenticated
app access denied
~~~

This is different from:

~~~text
redirect_uri rejected before authentication
~~~

and different again from:

~~~text
callback succeeded but local app session failed
~~~

Use the System Log to prove which one occurred.

## Case 6: unexpected MFA

When the user says:

> Okta suddenly asks for MFA.

Do not begin with the Custom Authorization Server access policy.

For Identity Engine, inspect:

~~~text
Global Session Policy
        |
        v
App sign-in / Authentication Policy
        |
        v
authenticator enrollment/state
        |
        v
existing Okta session context
        |
        v
other applicable context such as network/device/risk
~~~

The Global Session Policy and app sign-in policy are authentication-policy layers.

## Authorization Server access policy is not the MFA policy

### Authorization Server Access Policy

Controls token issuance conditions such as:

~~~text
client
grant type
requested scopes
user/group conditions
token lifetime
~~~

### Authentication policy layers

Control things such as:

~~~text
factor requirements
authentication assurance
reauthentication
session establishment
app-specific sign-in requirements
~~~

Do not change scope policy to fix an authentication-factor requirement unless evidence points there.

## Existing session context matters

Two tests can produce different prompts because their browser/session contexts differ.

Compare:

~~~text
same user?
same app?
same browser profile?
same existing Okta session?
same policy?
same authenticator enrollment?
same device/network context?
same test time?
~~~

A normal browser profile and a fresh private window do not necessarily have the same session state.

That difference is evidence.

## Case 7: local logout followed by immediate SSO

From Day 10:

~~~text
local application session destroyed
        |
        v
Okta browser session still active
        |
        v
new /authorize request
        |
        v
Okta can reuse SSO session
        |
        v
application creates new local session
~~~

Do not diagnose logout failed until you define which state was supposed to end.

Ask:

~~~text
Did local app session end?
Did app call Okta end-session?
Did browser retain Okta session?
Did app immediately enter a protected route and start /authorize again?
~~~

## Case 8: login loop

Draw one complete loop.

~~~text
App
 |
 | /login
 v
Okta
 |
 | callback
 v
App
 |
 | decides not authenticated
 v
/login
 |
 v
Okta
 |
 v
App
~~~

Then identify what succeeded on each cycle.

Possible causes include:

~~~text
local application session not created
session cookie not stored
session cookie not sent back
SPA token state not retained
callback processing failure
protected-route logic starts login too early
issuer/config mismatch
session invalidated immediately
~~~

A login loop does not prove Okta authentication is failing.

OAuth can succeed repeatedly while the application loses its own state.

## Case 9: cookie and local session problem

For a server-side application, inspect:

~~~text
Set-Cookie response header
cookie appears in browser?
domain
path
Secure
HttpOnly
SameSite
expiration
is cookie sent on next request?
~~~

Then inspect the server:

~~~text
session record exists?
session ID recognized?
session expired?
same node/session store?
~~~

Separate:

~~~text
browser did not store/send cookie
~~~

from:

~~~text
server received cookie but lost/rejected session
~~~

Those are different fixes.

## Okta browser cookies and browser privacy

Modern browser privacy controls can affect cross-site session-cookie behavior.

Current Okta Auth JS redirect guidance recommends a custom domain for reliable behavior across browsers because browser privacy features can interfere with Okta session cookies in some deployment shapes.

Do not diagnose every sign-in problem as third-party cookies.

Keep browser privacy and domain architecture in the evidence set when behavior differs by browser or profile.


## Case 10: works in Postman, fails in browser

This is useful evidence.

Postman proves:

~~~text
that specific HTTP request worked outside browser security/runtime behavior
~~~

It does not prove:

~~~text
browser redirect handling
CORS
cookie behavior
browser storage
callback routing
SPA transaction state
mixed content
browser privacy behavior
application JavaScript
~~~

Therefore:

~~~text
Postman works
+
browser fails
~~~

moves browser-specific layers higher in the investigation.

It does not automatically prove the complete browser integration is configured correctly.

## Case 11: CORS

CORS is enforced by browsers.

Server-to-server clients such as:

~~~text
Python
Postman
curl
backend Web Application
~~~

are not blocked by browser CORS enforcement.

Browser JavaScript can be.

The first question is:

> Which browser request is cross-origin?

Record:

~~~text
page origin
target origin
HTTP method
request headers
preflight OPTIONS present?
response Access-Control-Allow-* headers
browser Console error
~~~

Do not start by adding origins randomly.

## Your own API vs Okta Trusted Origins

These are different configuration owners.

### Browser SPA calls your Employee API

Example:

~~~text
SPA:
http://localhost:5173

API:
http://localhost:7000
~~~

If browser JavaScript calls the Employee API directly, your Employee API must return the appropriate CORS response for the SPA origin.

Adding an Okta Trusted Origin does not configure CORS on your Flask, Java, Node, or other application API.

### Browser JavaScript calls an Okta API using the Okta session cookie

Okta Trusted Origins can be relevant.

Okta requires explicitly permitted origins for supported cookie/session-based cross-origin calls.

### Browser uses an OAuth bearer token to call a supported Okta API

Okta documents an important distinction:

~~~text
Bearer-token Okta API request
-> does not rely on the Okta session cookie
-> Trusted Origin is not required for cookie-based trust
~~~

Do not use:

~~~text
CORS error
-> always add Trusted Origin
~~~

as a troubleshooting rule.

## Endpoint CORS support matters

Even with a trusted origin, not every operation is automatically browser-callable.

Okta documents CORS support per API operation.

For your own API, your framework's CORS configuration decides what the browser receives.

Always ask:

~~~text
Does the endpoint support this browser call?
Does the server allow this origin?
Does it allow this method?
Does it allow required headers?
Are credentials involved?
~~~

## Preflight requests

Browser JavaScript may send:

~~~http
OPTIONS /resource
Origin: http://localhost:5173
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization
~~~

before the actual request.

If the preflight fails, the browser may never send the protected GET or POST.

That creates a useful troubleshooting question:

> Did my API receive the real request, or only the preflight?

## Case 12: wrong app type

Architecture and app registration must agree.

Examples:

~~~text
SPA
-> public client
-> no protected client secret

Server-side Web Application
-> confidential client
-> client authentication
~~~

If a browser public client is configured as a confidential client that requires a secret, the flow can fail at token exchange.

Do not repair that by embedding a secret into JavaScript.

Fix the app/client architecture.

## Case 13: callback reached SPA but SPA remains signed out

Prove:

~~~text
callback URL reached?
code/state returned?
token request attempted?
token request succeeded?
callback parsing succeeded?
tokens entered token manager?
auth-state manager updated?
application route/UI recognized auth state?
~~~

Possible result:

~~~text
OAuth succeeded
but
SPA application state failed
~~~

Do not restart authentication-policy troubleshooting after token issuance is already proven.

## Case 14: callback reached Web Application but user still appears signed out

Prove:

~~~text
callback reached?
state validated?
backend /token succeeded?
ID token validated?
local session created?
Set-Cookie returned?
cookie stored?
cookie sent back?
server found session?
~~~

This is one of the strongest examples of:

~~~text
OIDC authentication success
!=
application-session success
~~~

## Case 15: environment works in dev, fails in prod

Compare environment values systematically.

~~~text
issuer
client ID
app type
redirect URI
sign-out URI
browser origin
Trusted Origin need
custom domain
HTTPS
cookie Secure/SameSite/domain
application base URL
reverse proxy headers
load balancer
session-store sharing
policy assignment
app assignment
authorization-server policy
~~~

Do not copy dev settings into production one line at a time until it starts working.

Create a difference table.

## Environment comparison table

| Setting | Dev | Prod | Same intentionally? |
|---|---|---|---|
| Issuer |  |  |  |
| Client ID |  |  |  |
| App type |  |  |  |
| Redirect URI |  |  |  |
| Sign-out URI |  |  |  |
| Browser origin |  |  |  |
| Trusted Origin need |  |  |  |
| HTTPS |  |  |  |
| Cookie settings |  |  |  |
| App sign-in policy |  |  |  |
| Controlled Access |  |  |  |
| Assignment |  |  |  |

Treat an environment mismatch as a hypothesis you prove from the table.

## Use System Log as correlated evidence

Okta's System Log is especially useful for:

~~~text
user sign-in
session creation
SSO to app
assignment changes
policy evaluation
failed authentication
~~~

Do not read one isolated row and stop.

Correlate related events when possible using:

~~~text
transaction.id
authenticationContext.externalSessionId
authenticationContext.rootSessionId
time
user
application/client
~~~

A System Log success also does not prove:

~~~text
your callback route executed correctly
your backend created a local session
your SPA stored tokens
your browser accepted your app cookie
~~~

Those are application/browser facts.

## The last-successful-step decision sequence

### Browser never left app

Investigate:

~~~text
application click/route
JavaScript error
configuration initialization
SDK initialization
~~~

### Browser reached /authorize but Okta rejected request

Investigate:

~~~text
client ID
redirect URI
issuer/endpoint
request parameters
app status
~~~

### User reached sign-in but access or authentication was denied

Investigate:

~~~text
assignment/Controlled Access
user state
Global Session Policy
app sign-in policy
authenticator state
routing/IdP if relevant
System Log
~~~

### Callback reached app but app rejects it

Investigate:

~~~text
state
pending transaction
callback route
code
transaction cookie/storage
~~~

### /token failed

Investigate:

~~~text
code
PKCE verifier
redirect URI
client authentication
issuer/token endpoint
code reuse/expiry
~~~

Day 14 goes deeper into token-endpoint failures.

### Tokens validated but app still says signed out

Investigate:

~~~text
local app session
SPA auth state
cookie/storage
protected-route logic
~~~

### Browser API call fails while Postman works

Investigate:

~~~text
CORS
origin
preflight
browser headers
cookie/privacy
mixed content
JavaScript request construction
~~~

## Do not change multiple controls at once

Bad troubleshooting:

~~~text
change redirect URI
add Trusted Origin
change policy
clear cookies
change issuer
restart app
~~~

Then:

> It works now.

You do not know why.

Better:

~~~text
1. Capture baseline failure.
2. State one hypothesis.
3. Change one relevant control.
4. Repeat the same transaction.
5. Compare evidence.
6. Restore temporary diagnostic changes.
~~~

## Distinguish observation from interpretation

### Observation

~~~text
Browser Network:
callback request contains code and state

Backend log:
State validation passed

Backend log:
No token exchange success
~~~

### Interpretation

~~~text
Browser authorization reached the callback.
Failure occurs at or after backend token exchange.
~~~

Do not write:

> Okta is broken.

That is not evidence.

## Incident note quality

Weak:

> Login failed because CORS. Added origin and fixed it.

Strong:

~~~text
Observed symptom:
SPA returned from sign-in, but browser API request failed.

Last confirmed successful step:
OAuth callback processed and access token was present.

First failed step:
Browser preflight to Employee API.

Evidence:
OPTIONS response did not allow http://localhost:5173.
The same API GET succeeded in Postman.

Root cause:
Employee API CORS policy did not allow the SPA development origin.

Change:
Allowed only the SPA development origin on the Employee API.

Proof:
OPTIONS succeeded and browser sent the subsequent GET successfully.
~~~

The strong note can be reviewed and repeated.

## Safe policy testing

Do not casually edit a broad Global Session Policy or shared app sign-in policy just to create a lab failure.

Prefer:

~~~text
dedicated test app
dedicated test user/group
narrow app sign-in policy
temporary change
restore immediately after evidence capture
~~~

The same principle applies to assignment testing.

Do not unassign your only administrator or only test identity.

## Common mistakes

### Mistake 1: Start with a favorite cause

Examples:

~~~text
always assignment
always cookies
always CORS
always policy
~~~

Wrong.

Find the failed checkpoint first.

### Mistake 2: Treat all policies as one policy

Wrong.

Authentication policies and Authorization Server access policies solve different problems.

### Mistake 3: Add Trusted Origin for every browser error

Wrong.

Identify the actual cross-origin request and authorization model.

### Mistake 4: Treat Postman success as proof browser config is correct

Wrong.

Postman does not reproduce browser runtime enforcement.

### Mistake 5: Treat successful Okta authentication as proof app session exists

Wrong.

The application still creates and retains its own authenticated state.

### Mistake 6: Clear cookies before collecting evidence

You can destroy the state that explains the incident.

Capture first.

### Mistake 7: Copy live credentials into a ticket

Never.

Use safe metadata.

### Mistake 8: Change Global Session Policy casually

It can affect many applications and users.

Use a narrow test policy/group where possible.

### Mistake 9: Unassign your only admin/test identity carelessly

Use a disposable test user or group.

Do not lock yourself out of the lab.

### Mistake 10: Call a nonce failure a state failure

They protect different transaction stages.

### Mistake 11: Diagnose a login loop without drawing one cycle

You need to know which step repeats.

### Mistake 12: Ignore environment differences

A correct dev flow does not prove production values match.

## What you should be able to explain

1. What is the last-successful-step method?
2. What evidence belongs in Browser Network?
3. What does System Log prove well?
4. What does System Log not prove about your application?
5. How do you prove a redirect URI mismatch?
6. What is the difference between missing transaction state and state mismatch?
7. Where does nonce validation occur?
8. How do you troubleshoot an issuer problem?
9. When does app assignment matter?
10. What does Controlled Access change?
11. Which policy layers should you inspect for unexpected MFA?
12. Why should you not begin with Authorization Server access policies for an MFA prompt?
13. Why can local logout be followed by immediate SSO?
14. How do you break a login loop into checkpoints?
15. How do you distinguish browser cookie failure from server session-store failure?
16. Why does Postman success not prove the SPA is correct?
17. What is CORS?
18. Who configures CORS when the SPA calls your own API?
19. When are Okta Trusted Origins relevant?
20. Why do bearer-token calls to supported Okta APIs not necessarily need Trusted Origins?
21. Why does endpoint CORS support matter?
22. What does a preflight prove?
23. Why can OAuth succeed while the UI still shows signed out?
24. How do you compare dev and prod systematically?
25. What makes a troubleshooting note evidence-based?

## Day 13 lab

[Day 13 Lab - Browser and Authentication Troubleshooting](../labs/day-13-browser-auth-troubleshooting.md)

The lab reuses:

~~~text
Day 7 server-side Web Application
Day 7 browser SPA
Day 10 session lifecycle app
Okta System Log
Browser DevTools
~~~

and adds one small local CORS evidence helper.

You will diagnose deliberately broken cases without reading the answer first.

## Day 13 completion standard

Day 13 is complete when you can take:

> Login does not work.

and turn it into:

~~~text
Browser left app?
        |
Reached Okta?
        |
/authorize accepted?
        |
User authenticated?
        |
App access/policy allowed?
        |
Callback returned?
        |
State/transaction valid?
        |
/token succeeded?
        |
OIDC response validated?
        |
Local application auth state created?
        |
Browser stored/sent required app state?
~~~

You should be able to investigate:

~~~text
redirect mismatch
wrong issuer
assignment
unexpected MFA
state/transaction loss
nonce failure
cookie/session failure
login loop
CORS
Trusted Origins
Postman-vs-browser differences
dev-vs-prod differences
~~~

without changing unrelated configuration.

## Official references

- [Okta: Configure a global session policy and app sign-in policies](https://developer.okta.com/docs/guides/configure-signon-policy/main/)
- [Okta: Policies](https://developer.okta.com/docs/concepts/policies/)
- [Okta: Sign users in using the redirect model](https://developer.okta.com/docs/guides/auth-js-redirect/main/)
- [Okta: Enable CORS](https://developer.okta.com/docs/guides/enable-cors/main/)
- [Okta: System Log query and event correlation](https://developer.okta.com/docs/reference/system-log-query/)
- [Okta: Create an app integration](https://developer.okta.com/docs/guides/create-an-app-integration/-/main/)
