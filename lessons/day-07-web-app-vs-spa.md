# Day 7 - Server-Side Web App vs Browser SPA

## Goal for today

Days 1 through 6 taught the protocol pieces separately.

Today you put those pieces into two real application architectures and compare where the OAuth responsibility lives.

You will implement:

~~~text
Architecture A
Server-side Web Application
Python Flask backend is the OAuth/OIDC client

Architecture B
Browser Single-Page Application
Browser JavaScript is the OAuth/OIDC client
~~~

Both use redirect authentication.

Both can use Authorization Code with PKCE.

The important difference is not the name of the application.

The important difference is:

> Which component owns the OAuth transaction, token exchange, token storage, and application session?

By the end of Day 7, you should understand:

- what the browser does in both architectures
- what the backend does in a server-side Web Application
- what the browser JavaScript does in a SPA
- who generates and retains state, nonce, and the PKCE verifier
- who calls /token
- where client authentication happens
- where OAuth tokens live
- what the browser holds after sign-in
- why a server-side application can give the browser an application-session cookie instead of OAuth tokens
- why a SPA cannot keep a client secret
- how browser token storage changes the attack surface
- what a Backend for Frontend, or BFF, changes
- why "Postman works" does not prove the browser architecture is correct
- how to tell an OAuth failure from a local application-session failure

[Open the Day 7 flow diagrams](../diagrams/day-07-web-app-vs-spa.md)

## The same user requirement can produce different architectures

Assume the business requirement is:

> Employees open an Employee Portal and sign in with Okta.

That requirement does not tell you where the OAuth client logic must run.

Two designs can satisfy it.

### Design A

~~~text
Browser
   |
   v
Python Web Application
   |
   v
Okta
~~~

The Python backend is the OIDC client.

### Design B

~~~text
Browser
   |
   v
JavaScript SPA
   |
   v
Okta
~~~

The SPA code running in the browser is the OIDC client.

The user sees a browser in both designs.

The trust boundary is different.

## Redirect authentication stays the same at the user level

Okta recommends redirect authentication for normal sign-in scenarios.

At a high level, both applications do this:

~~~text
Application
    |
    | redirect browser
    v
Okta-hosted sign-in
    |
    | user authenticates
    v
Okta redirects browser
    |
    v
Application callback
~~~

What happens after and around that redirect depends on the application architecture.

## Architecture A: server-side Web Application

Start with the full shape.

~~~text
Browser
   |
   | GET /login
   v
Web Application Backend
   |
   | create state, nonce, verifier
   | store transaction server-side
   |
   | 302 to Okta /authorize
   v
Browser
   |
   v
Okta
   |
   | user authenticates
   |
   | 302 callback?code=...&state=...
   v
Browser
   |
   | GET /callback?code=...&state=...
   v
Web Application Backend
   |
   | validate state
   | POST /token from backend
   | client authentication
   | code_verifier
   v
Okta
   |
   | tokens
   v
Web Application Backend
   |
   | validate ID token
   | store OAuth tokens server-side
   | create local application session
   |
   | Set-Cookie: app_session=<opaque-id>
   v
Browser
~~~

There are two different sessions or credential sets in this picture:

~~~text
OAuth/OIDC tokens
-> held by backend

Application session cookie
-> held by browser
~~~

Do not call those the same thing.

## Who is the OAuth client in the Web Application?

The backend.

Not the HTML page.

Not the user's browser.

The browser carries redirects, but the backend owns the OAuth transaction.

~~~text
OAuth/OIDC client:
Python Web Application Backend
~~~

That is why the Okta app integration is a:

~~~text
Web Application
~~~

and can be confidential.

## Where do state, nonce, and verifier live?

A server-side Web Application can keep transaction state on the server.

For example:

~~~text
Server-side pending transaction

transaction_id = random value
state          = random value
nonce          = random value
code_verifier  = random value
~~~

The browser may receive only a short opaque transaction cookie:

~~~text
day07_tx=abc123...
~~~

The actual verifier and expected state remain on the server.

When the callback returns, the backend uses that transaction identifier to recover the correct pending transaction.

This is one reason architecture matters.

## Who calls /token in the Web Application?

The backend.

~~~text
Python backend
      |
      | POST /token
      | client authentication
      | authorization code
      | redirect_uri
      | code_verifier
      v
Okta
~~~

The browser Network tab does not need to show this request because the request is not made by the browser.

This becomes an important troubleshooting clue.

## Where does the client secret live?

On the confidential backend.

~~~text
Environment variable
secret manager
vault
protected server configuration
~~~

For our training app, we use an environment variable.

We do not place the client secret into:

~~~text
HTML
JavaScript
browser storage
URL
GitHub
~~~

If the browser can read it, it is no longer a confidential client secret.

## Where do the tokens live?

In the Day 7 Web Application lab:

~~~text
ID token
access token
OAuth transaction data
        |
        v
server-side memory
~~~

The browser does not receive the raw OAuth tokens from our application.

The backend validates the ID token and creates a local application session.

## What is the local application session?

Successful OIDC authentication does not automatically create your application's own session.

The application decides how to represent:

> This browser is signed in to this application.

In our lab:

~~~text
Backend generates random session ID
        |
        v
Backend stores session record
        |
        v
Browser receives opaque session cookie
~~~

Conceptually:

~~~http
Set-Cookie: day07_session=<random-session-id>; HttpOnly; SameSite=Lax
~~~

On later requests:

~~~http
Cookie: day07_session=<random-session-id>
~~~

The backend looks up the session.

The browser does not need the OAuth tokens to render the signed-in application.

## Why HttpOnly matters

An HttpOnly cookie cannot normally be read through browser JavaScript.

That helps keep the application-session credential away from normal JavaScript access.

HttpOnly does not solve every web-security problem.

For example, cookie-based applications must still consider CSRF, cookie scope, HTTPS, Secure cookies, SameSite behavior, XSS, session fixation, session expiration, and server-side session protection.

Day 7 is not a browser-security course.

The important architecture point is:

> The Web Application can keep OAuth tokens on the backend and expose only an application-session cookie to the browser.

## Our localhost cookie is intentionally a lab simplification

Production session cookies should normally be sent over HTTPS and use appropriate Secure, HttpOnly, SameSite, lifetime, and domain/path settings.

Our local lab uses:

~~~text
http://localhost
~~~

so the sample cannot require a Secure cookie during local HTTP development.

Do not copy the localhost cookie settings directly into production.

## Architecture B: browser SPA

Now move the OAuth client into browser JavaScript.

~~~text
Browser SPA
   |
   | create OAuth transaction
   | state
   | nonce
   | PKCE verifier/challenge
   |
   | redirect to /authorize
   v
Okta
   |
   | user authenticates
   |
   | callback with code + state
   v
Browser SPA
   |
   | validate transaction
   | POST /token
   | code + verifier
   v
Okta
   |
   | tokens
   v
Browser SPA
~~~

There is no confidential backend OAuth client in this architecture.

The browser application is the client.

## Who is the OAuth client in the SPA?

~~~text
JavaScript application running in browser
~~~

That makes it a public client.

The user controls the browser environment.

Therefore the SPA cannot safely depend on a long-lived client secret.

~~~text
SPA
-> client ID
-> Authorization Code + PKCE
-> client authentication = none
~~~

## Who calls /token in the SPA?

The browser client.

A maintained SPA OAuth/OIDC library normally handles this.

In our Day 7 lab, we use Okta Auth JS rather than manually rebuilding the browser flow again.

That is deliberate.

Day 3 taught the raw protocol manually.

Day 7 teaches how an application should delegate protocol details to a maintained library while you still understand what the library is doing.

Okta recommends existing libraries and OAuth helper methods instead of hand-building production protocol code.

## What Auth JS does for the SPA

At a high level, Auth JS handles work such as:

~~~text
generate transaction values
build authorization request
perform redirect
recognize callback
exchange authorization code
validate returned OAuth/OIDC response
manage tokens
maintain application auth state
~~~

You should still be able to trace the HTTP requests because you learned the protocol first.

A library should reduce implementation mistakes.

It should not turn the protocol into a mystery.

## Where do SPA tokens live?

A browser SPA has to manage tokens in the browser environment unless the architecture introduces a backend layer such as a BFF.

Browser choices can include:

~~~text
in-memory storage
session storage
local storage
other protected browser-supported mechanisms
~~~

Each has tradeoffs.

Our Day 7 SPA lab intentionally configures:

~~~text
sessionStorage
~~~

because it makes the location visible and keeps the lab state scoped to the browser tab/session.

This is not a statement that sessionStorage is always the correct production choice.

## Browser storage and XSS

Anything accessible to browser JavaScript can potentially be exposed if hostile JavaScript executes in the application origin.

That includes OAuth tokens held in JavaScript-accessible storage.

Think:

~~~text
SPA stores token in browser-accessible location
        |
        v
malicious script executes in application origin
        |
        v
script may access token
~~~

Changing from localStorage to sessionStorage does not magically remove XSS risk.

In-memory storage reduces persistence, but malicious JavaScript executing at the right time can still access application state.

The real design question is broader:

> Do OAuth tokens need to be available to browser JavaScript at all?

## Backend for Frontend

A BFF changes the SPA architecture.

Instead of:

~~~text
Browser SPA
    |
    | OAuth tokens
    v
APIs
~~~

a BFF can use:

~~~text
Browser
   |
   | application session cookie
   v
BFF
   |
   | OAuth access token
   v
Downstream API
~~~

The BFF manages OAuth tokens on the server.

The browser talks only to the BFF using its application session.

Okta currently documents BFF as a token-management model that moves sensitive access and refresh tokens to a trusted server layer and gives the browser a secure session cookie instead.

Our Day 7 Web Application demonstrates the same core trust idea:

~~~text
tokens on server
session cookie in browser
~~~

It is not yet a complete production BFF because we are not proxying a downstream API in this lab.

Day 8 introduces the protected API.

## Server-side Web Application vs SPA

Use this comparison.

| Question | Server-side Web Application | Browser SPA |
|---|---|---|
| OAuth client runs where? | Backend server | Browser JavaScript |
| Public or confidential? | Confidential | Public |
| Can protect client secret? | Yes | No |
| Browser carries /authorize redirect? | Yes | Yes |
| Who owns state/nonce/verifier? | Backend can store server-side | Browser client/library |
| Who calls /token? | Backend | Browser client/library |
| Client authentication? | Yes, for confidential client | none |
| PKCE? | Can and should be used in our design | Yes |
| OAuth tokens stored where in our lab? | Server memory | Browser token manager/sessionStorage |
| Browser receives raw OAuth tokens from app? | No | Browser client owns them |
| Browser uses local app-session cookie? | Yes | Not in the simple SPA model |
| Main token-exposure concern | Backend compromise/session design | Browser JavaScript/XSS |

Do not use this table to decide that one architecture is universally better.

Choose based on application requirements and security architecture.

## Browser Network tab looks different

This is one of the most useful Day 7 observations.

### Server-side Web Application

The browser can see:

~~~text
GET /login
302 to Okta
GET /authorize
Okta authentication
302 back to /callback
GET /callback?code=...&state=...
Set-Cookie for application session
~~~

The browser normally does not see:

~~~text
backend POST /token
client secret
backend token response
server-side token storage
~~~

### SPA

The browser can see:

~~~text
authorization redirect
callback
browser-side token exchange
token-related browser activity
browser storage
~~~

The browser is the OAuth client environment.

That difference tells you where to troubleshoot.

## Application session failure is not necessarily OAuth failure

Server-side example:

~~~text
/authorize succeeded
callback succeeded
/token succeeded
ID token validated
        |
        v
application fails to create local session
        |
        v
user still appears signed out
~~~

It would be wrong to conclude:

> Okta authentication failed.

The OAuth/OIDC transaction succeeded.

The application's local session logic failed afterward.

This is exactly why Day 7 exists.

## SPA application-state failure is also different

SPA example:

~~~text
OAuth redirect succeeds
tokens are obtained
        |
        v
application auth-state code fails
        |
        v
UI still renders "signed out"
~~~

Again:

~~~text
protocol success
!=
application-state success
~~~

You must prove where the transaction stopped.

## Okta session vs application session

Do not fully merge these concepts yet.

For today, recognize:

~~~text
Okta browser session
-> session with Okta
-> supports SSO behavior

Web Application local session
-> session between browser and your application

SPA token state
-> browser application's OAuth/OIDC state
~~~

These can exist or disappear independently.

Day 10 studies session and logout behavior in depth.

## Why Postman can mislead you

Postman is excellent for controlled HTTP testing.

It does not reproduce all browser behavior.

A token request succeeding in Postman proves:

~~~text
that request worked
~~~

It does not prove:

~~~text
SPA callback handling works
browser transaction state survived
browser storage works
application routing works
CORS behavior is correct
browser cookie behavior is correct
local application session logic works
~~~

So:

> "It works in Postman" is evidence, not a complete architecture diagnosis.

## CORS and Trusted Origins need precise reasoning

CORS is a browser security mechanism.

A server-to-server Web Application request is not blocked by browser CORS because the browser is not making that backend HTTP call.

A SPA can encounter CORS restrictions because browser JavaScript makes cross-origin requests.

Okta also has Trusted Origins configuration for browser origins that are permitted to access supported Okta APIs or participate in specific browser behaviors.

Do not use this troubleshooting pattern:

~~~text
browser error
-> add Trusted Origin
-> hope
~~~

Instead:

~~~text
Which browser request failed?
Which origin made it?
Which endpoint received it?
Does that endpoint support CORS?
Is the application origin supposed to be trusted for this operation?
~~~

Day 13 goes deeper into browser failures.

## Redirect model vs embedded authentication

Both Day 7 implementations use:

~~~text
Redirect model
~~~

The user is sent to the Okta-hosted sign-in experience.

We are not building a custom username/password form that directly authenticates against Okta.

Okta currently recommends the redirect model for most integrations because Okta hosts and maintains the sign-in experience and can apply the configured authentication policies.

Embedded authentication is a different architecture.

Recognize the distinction, but do not divert this course into embedded Identity Engine flows.

## What production applications should use

The lab exposes architecture.

It is not a reason to build every production OIDC implementation from low-level HTTP calls.

For production:

~~~text
SPA
-> use a maintained OIDC/OAuth client library such as Okta Auth JS where appropriate

Server-side web app
-> use maintained OIDC middleware/library appropriate to the framework
~~~

Our Python server sample is intentionally readable so you can see each responsibility.

It is not a complete production session framework.

## Common mistakes

### Mistake 1: The browser redirected, so the browser must be the OAuth client

Wrong.

In a server-side Web Application, the browser carries redirects while the backend is the OAuth client.

### Mistake 2: The Web Application should send its client secret to the browser

Wrong.

The client secret stays on the confidential backend.

### Mistake 3: Successful Okta login means the local application session exists

Wrong.

The application still has to create and maintain its own session if that architecture uses one.

### Mistake 4: A SPA can hide its secret in an environment file

Wrong.

If that environment value is compiled or delivered to the browser, the user can obtain it.

### Mistake 5: sessionStorage solves XSS

Wrong.

It changes persistence behavior. JavaScript-accessible credentials can still be exposed to hostile JavaScript.

### Mistake 6: Postman success proves the SPA is configured correctly

Wrong.

Postman does not reproduce browser state, routing, storage, cookie, or CORS behavior.

### Mistake 7: Every SPA should automatically become a BFF

Wrong.

BFF is an architectural choice with security benefits and infrastructure/complexity tradeoffs.

### Mistake 8: Every browser problem is CORS

Wrong.

Trace the failing request first.

## What you should be able to explain

1. Who is the OAuth client in a server-side Web Application?
2. Who is the OAuth client in a SPA?
3. Who calls /token in each architecture?
4. Where does the Web Application client secret live?
5. Where can the Web Application keep state, nonce, and verifier?
6. What does the browser hold after our Web Application signs in?
7. Where do OAuth tokens live in our Web Application lab?
8. Where do OAuth tokens live in our SPA lab?
9. Why does a SPA not have a useful confidential client secret?
10. Why can browser token storage increase XSS impact?
11. What does a BFF change?
12. Why can OAuth succeed while the local Web Application session fails?
13. Why does Postman success not prove browser success?
14. Why is browser Network evidence different between the two architectures?

## Day 7 lab

[Day 7 Lab - Run a Web Application and a SPA](../labs/day-07-web-app-vs-spa.md)

The lab runs both architectures and compares the evidence side by side.

## Day 7 completion standard

Day 7 is complete when you can draw both architectures from memory and fill in:

~~~text
OAuth client:
public/confidential:
who starts /authorize:
who retains PKCE verifier:
who handles callback:
who calls /token:
where client credential lives:
where ID/access tokens live:
what the browser stores:
what creates application auth state:
what browser DevTools can prove:
what only backend evidence can prove:
~~~

You should also be able to look at a failure and say whether it belongs to:

~~~text
Okta authentication
OAuth authorization response
token exchange
token validation
browser transaction state
backend transaction state
local application session
SPA auth state
browser security/CORS
~~~

without calling all of them "OAuth problems."

## Official references

- [Okta: Sign users in to a web app using the redirect model](https://developer.okta.com/docs/guides/sign-into-web-app-redirect/main/)
- [Okta: Python web app redirect quickstart](https://developer.okta.com/docs/guides/sign-into-web-app-redirect/python/main/)
- [Okta: Sign users in to a SPA using the redirect model](https://developer.okta.com/docs/guides/sign-into-spa-redirect/main/)
- [Okta: Auth JS](https://github.com/okta/okta-auth-js)
- [Okta: Redirect vs embedded deployment models](https://developer.okta.com/docs/concepts/redirect-vs-embedded/)
- [Okta: Manage user credentials and BFF token storage](https://developer.okta.com/docs/concepts/manage-user-creds/)
