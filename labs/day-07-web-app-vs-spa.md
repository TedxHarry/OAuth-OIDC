# Day 7 Lab - Run a Web Application and a SPA

## Purpose

This lab compares two real OIDC application architectures.

You will run:

~~~text
A. Python server-side Web Application
B. Browser SPA using Okta Auth JS
~~~

Both use redirect authentication with Okta.

The goal is not merely to make both applications sign in.

The goal is to prove:

~~~text
who is the OAuth client
who owns the PKCE transaction
who calls /token
where client authentication happens
where OAuth tokens live
what the browser stores
what creates application auth state
~~~

Complete the lesson first:

[Day 7 - Server-Side Web App vs Browser SPA](../lessons/day-07-web-app-vs-spa.md)

Use the diagrams while running the lab:

[Day 7 Flow Diagrams](../diagrams/day-07-web-app-vs-spa.md)

## Important scope boundary

Day 7 is about application architecture and sign-in.

We are **not** protecting our own Employee API yet.

The access tokens in these Day 7 sign-in labs come from the Okta Org Authorization Server and are not used as custom Employee API tokens.

Day 8 introduces the API.

## Tools

You need:

~~~text
Okta integration tenant
Chrome or Edge
Python
Postman, optional for comparison
Node.js 20 or newer for the SPA
npm
~~~

Check Node:

~~~powershell
node --version
~~~

The Day 7 SPA currently uses:

~~~text
@okta/okta-auth-js 8.0.1
Vite 8.3.0
~~~

The versions are pinned in the lab package so the exercise does not silently change underneath the learner.

## Part 1 - Prepare the server-side Web Application integration

Reuse the Web Application created on Day 6.

Open its General settings.

Keep the existing redirect URI if you want, and add:

~~~text
http://localhost:5000/callback
~~~

Confirm:

~~~text
Application type:
Web Application

Authorization Code:
enabled

Client ID:
available

Client Secret:
available
~~~

Do not put the client secret into this repository.

## Part 2 - Prepare the Python environment

Activate the Python virtual environment you used on Day 5, or create one.

Install the Day 7 dependencies:

~~~powershell
python -m pip install Flask requests "PyJWT[crypto]"
~~~

Set environment variables in the same PowerShell window.

~~~powershell
$env:OKTA_ISSUER="https://YOUR-OKTA-DOMAIN"
$env:OKTA_CLIENT_ID="YOUR-WEB-CLIENT-ID"
$env:OKTA_CLIENT_SECRET="YOUR-WEB-CLIENT-SECRET"
~~~

Use the Org Authorization Server issuer:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

Do not use the Admin Console hostname containing -admin.

## Part 3 - Start the Web Application

Run:

~~~powershell
python scripts/python/day07_web_app.py
~~~

Expected startup information:

~~~text
Day 7 server-side Web Application
Issuer: ...
Redirect URI: http://localhost:5000/callback
Open: http://localhost:5000
~~~

Open:

~~~text
http://localhost:5000
~~~

## Part 4 - Open browser evidence tools before signing in

Open DevTools.

Enable:

~~~text
Network
Preserve log
~~~

Also open:

~~~text
Application
  |
  v
Cookies
  |
  v
http://localhost:5000
~~~

Do not sign in yet.

Record:

~~~text
day07_session cookie present before login?:
~~~

Expected:

~~~text
No
~~~

## Part 5 - Sign in to the server-side Web Application

Click:

~~~text
Sign in with Okta
~~~

Complete Okta authentication if prompted.

After the callback, the application should show:

~~~text
Signed in to this local application
~~~

The page also shows a safe summary of validated ID-token claims.

The raw tokens are not rendered.

## Part 6 - Trace the browser-side Web Application flow

From DevTools Network, identify:

~~~text
GET /login
302 redirect
Okta /authorize request
Okta authentication traffic
302 callback
GET /callback?code=...&state=...
final GET /
~~~

Record:

~~~text
Did browser see authorization code?:
Did browser carry returned state?:
Did callback reach localhost:5000?:
~~~

Expected:

~~~text
Yes
Yes
Yes
~~~

The browser is carrying the front-channel response.

That does not make the browser the confidential OAuth client.

## Part 7 - Look for /token in Browser Network

Search the browser Network log for:

~~~text
/token
~~~

For the Web Application token exchange, you should **not** find a browser-originated /token request.

Now look at the Python terminal.

You should see messages similar to:

~~~text
State validation passed
Backend is now calling /token
Backend token exchange succeeded
ID token validation succeeded
Creating local application session
~~~

Explain:

~~~text
Browser carried callback
but
backend called /token
~~~

This is one of the most important Day 7 observations.

## Part 8 - Inspect the local application-session cookie

In DevTools:

~~~text
Application
  |
  v
Cookies
  |
  v
http://localhost:5000
~~~

Find:

~~~text
day07_session
~~~

Inspect:

~~~text
HttpOnly:
SameSite:
Value shape:
~~~

Do not copy the cookie value into your notes.

The cookie value is only an opaque random identifier.

The raw OAuth tokens are stored server-side in this lab.

## Part 9 - Prove tokens are server-side

Open:

~~~text
http://localhost:5000/debug/session
~~~

The page reports safe booleans such as:

~~~text
id_token_present_server_side
access_token_present_server_side
refresh_token_present_server_side
raw_tokens_rendered_to_browser
~~~

Expected:

~~~text
raw_tokens_rendered_to_browser = False
~~~

Now inspect page source and browser storage.

You should not find the raw Web Application OAuth tokens intentionally rendered by the sample.

## Part 10 - Destroy only the local Web Application session

Click:

~~~text
Destroy local application session
~~~

The app deletes:

~~~text
server-side application-session record
day07_session browser cookie
~~~

It does **not** perform Okta logout.

You should now appear signed out to the local application.

If you click Sign in again, Okta may sign you in without another credential prompt because the Okta browser session can still exist. Exact prompts depend on your Okta session and authentication policies.

Record:

~~~text
Local application session removed?:
Okta credential prompt shown again?:
~~~

Do not draw a final conclusion about logout yet.

Day 10 studies that behavior fully.

## Part 11 - Break the Web Application client secret

Stop the Python app.

Change only:

~~~powershell
$env:OKTA_CLIENT_SECRET="intentionally-wrong-secret"
~~~

Restart:

~~~powershell
python scripts/python/day07_web_app.py
~~~

Start a fresh sign-in.

Expected reasoning:

~~~text
/authorize can succeed
user authentication can succeed
callback can reach Web Application
state can validate
backend /token fails
local application session is not created
~~~

Record:

~~~text
Last successful browser step:
Backend failure:
HTTP/OAuth error shown:
day07_session created?:
~~~

Restore the correct secret before continuing.

## Part 12 - Break the server-side pending transaction

This test demonstrates why state and verifier storage are part of application architecture.

Start the Web Application with the correct secret.

Click Sign in.

While the browser is away at Okta, stop and restart the Python process before finishing the authorization flow.

Because the sample stores pending transactions only in memory, restarting the server clears:

~~~text
expected state
nonce
code_verifier
pending transaction record
~~~

Finish the Okta flow.

The callback should fail because the server no longer has the pending transaction.

This is **not** an Okta authentication failure.

Record:

~~~text
Okta authentication:
callback reached:
pending transaction found:
token request attempted:
root cause:
~~~

Expected:

~~~text
Okta authentication can succeed
callback can reach application
pending server-side transaction is gone
/token should not be attempted
~~~

Production systems use durable or shared session and transaction storage appropriate to their architecture.

The in-memory store is intentionally visible training code.

## Part 13 - Prepare the SPA app integration

Reuse the SPA integration created on Day 3.

Add this Sign-in redirect URI:

~~~text
http://localhost:5173/
~~~

Keep:

~~~text
Application type:
Single-Page Application

Client authentication:
None

Authorization Code:
enabled
~~~

Following Okta's SPA setup guidance, add a Trusted Origin for:

~~~text
http://localhost:5173
~~~

with CORS enabled if it is not already configured.

Do not add a client secret to the SPA.

## Part 14 - Install the SPA dependencies

Open a new terminal.

~~~powershell
cd scripts/day07_spa
npm install
~~~

The lab requires Node.js 20 or newer because the pinned dependency and tooling versions require a modern Node runtime.

Start the SPA:

~~~powershell
npm run dev
~~~

Open:

~~~text
http://localhost:5173/
~~~

## Part 15 - Configure the SPA locally

The page asks for:

~~~text
Okta issuer
SPA client ID
~~~

Enter:

~~~text
Issuer:
https://YOUR-OKTA-DOMAIN

Client ID:
the Day 3 SPA client ID
~~~

There is no client secret field.

That absence is part of the architecture.

The lab stores this non-secret configuration in browser sessionStorage so it survives the redirect in the same tab.

## Part 16 - Inspect SPA storage before sign-in

Before clicking Sign in, open:

~~~text
DevTools
  |
  v
Application
  |
  v
Session Storage
  |
  v
http://localhost:5173
~~~

You should see the Day 7 configuration entry.

Do not expect OAuth tokens yet.

Record:

~~~text
OAuth client runs where?:
Client secret present?:
Token manager storage configured as:
~~~

## Part 17 - Sign in to the SPA

Enable Preserve log in Network.

Click:

~~~text
Sign in with Okta
~~~

Complete authentication if prompted.

After redirect processing, the page should report safe booleans:

~~~text
authenticated_for_lab
id_token_present_in_browser_token_manager
access_token_present_in_browser_token_manager
refresh_token_present_in_browser_token_manager
raw_tokens_rendered_to_page
token_manager_storage
oauth_client_location
~~~

The page intentionally does not display raw token strings.

## Part 18 - Trace the SPA /token request

Search browser Network for:

~~~text
/token
~~~

Unlike the server-side Web Application, the SPA's token request is made from the browser client environment.

Inspect the request without copying credentials.

Identify:

~~~text
POST /token
grant_type=authorization_code
client_id
redirect_uri
code
code_verifier
~~~

Confirm:

~~~text
client_secret absent
~~~

This is the browser-side public-client flow.

## Part 19 - Inspect SPA token storage

Open:

~~~text
Application
  |
  v
Session Storage
  |
  v
http://localhost:5173
~~~

Auth JS manages its token state in browser storage according to the lab configuration.

Do not copy live tokens.

Record only:

~~~text
ID token appears to be managed in browser environment?:
Access token appears to be managed in browser environment?:
Storage type:
~~~

Compare this with the Web Application:

~~~text
Web Application:
tokens server-side

SPA:
tokens in browser client environment
~~~

## Part 20 - Clear only the SPA local tokens

Click:

~~~text
Clear local SPA tokens
~~~

The page should show that its local token manager no longer has the tokens.

This does not deliberately terminate the Okta browser session.

If you click Sign in again, Okta may use its existing session and return quickly.

Again, Day 10 covers this lifecycle in depth.

The Day 7 point is:

~~~text
SPA local token state
!=
Okta browser session
~~~

## Part 21 - Break SPA configuration with the wrong client ID

Click:

~~~text
Reset lab configuration
~~~

Enter the correct issuer but an intentionally invalid client ID.

Try Sign in.

Record:

~~~text
Did browser reach Okta?:
Where did the flow fail?:
What error was returned?:
Did any SPA tokens get stored?:
~~~

Then restore the correct client ID.

This failure occurs before a useful authenticated SPA state can be established.

## Part 22 - Compare Browser Network evidence side by side

Complete:

| Evidence | Server-side Web App | SPA |
|---|---|---|
| Browser sees /authorize |  |  |
| Browser sees callback code/state |  |  |
| Browser makes /token request |  |  |
| Client secret visible to browser |  |  |
| OAuth tokens managed in browser |  |  |
| Local app-session cookie used |  |  |
| Backend logs needed for token-exchange evidence |  |  |

Expected architecture:

| Evidence | Server-side Web App | SPA |
|---|---|---|
| Browser sees /authorize | Yes | Yes |
| Browser sees callback code/state | Yes | Yes |
| Browser makes /token request | No | Yes |
| Client secret visible to browser | No | No secret exists |
| OAuth tokens managed in browser | No | Yes |
| Local app-session cookie used | Yes | No in this simple SPA |
| Backend logs needed for token-exchange evidence | Yes | No backend OAuth client exists |

## Part 23 - Compare ownership

Fill this in from memory.

| Responsibility | Web Application | SPA |
|---|---|---|
| OAuth client |  |  |
| Public/confidential |  |  |
| state owner |  |  |
| nonce owner |  |  |
| PKCE verifier owner |  |  |
| /token caller |  |  |
| client authentication |  |  |
| OAuth token storage |  |  |
| browser application credential/state |  |  |

## Part 24 - Explain the BFF change

Do not build the BFF yet.

Explain this transformation:

~~~text
Simple SPA

Browser JS
  |
  | holds access token
  v
API


BFF

Browser
  |
  | HttpOnly application-session cookie
  v
BFF
  |
  | holds OAuth tokens
  | sends access token
  v
API
~~~

Answer:

1. Which component now owns OAuth tokens?
2. What credential does the browser use with the BFF?
3. What browser token-exposure risk is reduced?
4. What new infrastructure and session-security responsibilities are introduced?

## Part 25 - Correlate with Okta System Log

Run one successful Web Application sign-in and one successful SPA sign-in.

In Okta System Log, correlate by:

~~~text
time
application
client ID when available
authentication outcome
OAuth/OIDC events
~~~

The two applications have different client registrations.

Do not expect System Log alone to tell you where the local application stored its tokens.

That is application evidence.

Use:

~~~text
Browser Network
+
backend logs for Web Application
+
browser storage for SPA
+
Okta System Log
~~~

## Part 26 - Final evidence record

### Server-side Web Application

~~~text
OAuth client:
client type:
redirect URI:
who stored state/nonce/verifier:
who called /token:
client authentication:
where tokens were stored:
what browser stored:
was /token visible in Browser Network?:
local session cookie HttpOnly?:
wrong-secret failure:
lost-transaction failure:
~~~

### SPA

~~~text
OAuth client:
client type:
redirect URI:
who stored transaction state:
who called /token:
client authentication:
where tokens were stored:
what browser stored:
was /token visible in Browser Network?:
wrong-client-ID failure:
~~~

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Server-side Web Application

The backend is the confidential OAuth client.

The browser carries front-channel redirects and the callback request.

The backend owns the client secret, PKCE transaction, token request, token validation, OAuth tokens, and local application session.

The browser holds an opaque HttpOnly application-session cookie.

### SPA

Browser JavaScript is the public OAuth client.

It has no client secret.

The browser client or library owns the PKCE transaction, performs the token exchange, and manages OAuth tokens in the browser environment.

### Why the Network tabs differ

The server-side /token call is a backend HTTP request and therefore is not made by the browser.

The SPA /token call is a browser-client request and can appear in browser Network evidence.

### Why local logout can differ from Okta logout

Destroying the Web Application session or clearing SPA tokens changes local application state.

It does not automatically prove that the Okta browser session ended.

### BFF

A BFF moves OAuth tokens to a server and gives the browser an application-session cookie instead.

That reduces direct browser-JavaScript token exposure but adds backend and session infrastructure and security responsibilities.

</details>

## Day 7 completion check

You are ready for Day 8 when you can draw both application architectures without looking and explain:

~~~text
who is the OAuth client
who calls /token
where client authentication happens
where tokens live
what the browser holds
why browser evidence differs
why application-session failure is not automatically OAuth failure
what a BFF changes
~~~

Do not move on if the two flows still look like the same architecture with different programming languages.
