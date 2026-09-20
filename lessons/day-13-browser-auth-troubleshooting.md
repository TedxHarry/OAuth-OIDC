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
