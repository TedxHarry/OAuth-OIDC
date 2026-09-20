# Day 13 Lab - Browser and Authentication Troubleshooting

## Purpose

Day 13 is a troubleshooting day.

You are not learning another grant type.

You are learning to answer:

> Where did the transaction stop, and what evidence proves it?

You will use:

~~~text
Browser DevTools
Day 13 Web fault harness
Day 7 SPA
Day 10 session app
Day 13 CORS harness
Okta System Log
~~~

Complete the lesson first:

[Day 13 - Browser and Authentication Troubleshooting from Evidence](../lessons/day-13-browser-auth-troubleshooting.md)

Keep the diagrams open:

[Day 13 Troubleshooting Diagrams](../diagrams/day-13-browser-auth-troubleshooting.md)

## Safety rules

Do not record or share:

~~~text
authorization codes
access tokens
ID tokens
refresh tokens
PKCE verifiers
client secrets
session cookie values
~~~

Use safe evidence:

~~~text
URL path
HTTP status
redirect URI
client ID
issuer
state matched yes/no
nonce matched yes/no
token request attempted yes/no
token request succeeded yes/no
cookie present yes/no
System Log outcome
transaction ID
root/external session ID
~~~

## Part 1 - Prepare your incident-note template

For every case use:

~~~text
Observed symptom:

Last confirmed successful step:

First failed step:

Browser evidence:

Application evidence:

Okta System Log evidence:

Root cause:

Single change:

Proof after change:
~~~

Do not write the root cause until you have evidence.

## Part 2 - Prepare Browser DevTools

Open Chrome or Edge.

For every browser case:

~~~text
DevTools
  |
  +-- Network
  |     Preserve log = enabled
  |
  +-- Console
  |
  +-- Application
        Cookies
        Session Storage
        Local Storage
~~~

Do not clear browser state before capturing the failure.

## Part 3 - Prepare the Day 13 Web Application

Reuse the confidential Web Application client from Day 7.

Add this Sign-in redirect URI:

~~~text
http://localhost:5300/callback
~~~

Do not register:

~~~text
http://localhost:5300/wrong-callback
~~~

The wrong URI is intentionally used by one hidden case.

Confirm:

~~~text
Application type:
Web Application

Authorization Code:
enabled

Client ID:
available

Client secret:
available
~~~

## Part 4 - Start the Day 13 fault harness

Set:

~~~powershell
$env:OKTA_ISSUER="https://YOUR-OKTA-DOMAIN"
$env:OKTA_CLIENT_ID="YOUR-WEB-CLIENT-ID"
$env:OKTA_CLIENT_SECRET="YOUR-WEB-CLIENT-SECRET"
~~~

Run:

~~~powershell
python scripts/python/day13_web_faults.py
~~~

Open:

~~~text
http://localhost:5300
~~~

Do not open the Python source mapping while diagnosing Cases A through E.

## Part 5 - Establish a normal baseline

Click:

~~~text
Normal sign-in
~~~

Complete authentication if needed.

Record:

~~~text
Browser reached /authorize?:
Callback reached localhost:5300?:
State validation passed?:
Token request attempted?:
Token exchange succeeded?:
OIDC validation succeeded?:
Local session created?:
Final page status:
~~~

This is your healthy reference transaction.

## Part 6 - Correlate the healthy sign-in in System Log

Open:

~~~text
Reports
  |
  v
System Log
~~~

Use approximate time, user, and application to locate the sign-in.

When visible, record:

~~~text
event type:
outcome:
transaction.id:
externalSessionId:
rootSessionId:
~~~

Do not expect the System Log to show:

~~~text
day13_session cookie
Python in-memory session record
~~~

Those belong to the local application.

## Part 7 - Diagnose Case A without reading the source

Return to:

~~~text
http://localhost:5300
~~~

Click:

~~~text
Case A
~~~

Do not fix anything yet.

Record:

~~~text
Did browser leave app?:
Did browser reach Okta?:
Actual redirect_uri in /authorize:
Did callback reach localhost:5300/callback?:
Did backend report callback_reached=True?:
Was /token attempted?:
~~~

Write:

~~~text
Last confirmed successful step:
First failed step:
Hypothesis:
~~~

## Part 8 - Prove or reject your Case A hypothesis

Compare:

~~~text
actual redirect_uri
~~~

with:

~~~text
registered Sign-in redirect URIs
~~~

Do not change the registered configuration.

If the values differ, write the exact mismatch.

Then prove:

~~~text
Normal sign-in
-> succeeds
~~~

## Part 9 - Diagnose Case B

Click:

~~~text
Case B
~~~

Record:

~~~text
Browser reached Okta?:
Authentication completed?:
Callback reached app?:
Transaction cookie present?:
pending_transaction_found:
token_request_attempted:
~~~

Do not classify it as state mismatch unless an expected state actually exists and differs.

Write the first failed step.

## Part 10 - Explain Case B architecture

Answer:

~~~text
Could Okta authentication have succeeded?:

Did the callback reach the application?:

What application-side object was unavailable?:

Would changing MFA policy repair it?:
~~~

Then run Normal sign-in again as proof that Okta itself is not generally unavailable.

## Part 11 - Diagnose Case C

Click:

~~~text
Case C
~~~

Record:

~~~text
Callback reached?:
pending_transaction_found:
returned state present?:
state_validation:
token_request_attempted:
~~~

Write:

~~~text
What did the application still have?:

What comparison failed?:

How is this different from Case B?:
~~~

## Part 12 - Diagnose Case D

Click:

~~~text
Case D
~~~

Record:

~~~text
Callback reached?:
state_validation:
token_request_attempted:
token_exchange:
OIDC validation:
local_session_created:
~~~

Question:

> Which case traveled further, Case C or Case D?

Prove your answer from the stage logs.

## Part 13 - Separate state from nonce

For Case C and Case D complete:

| Question | Case C | Case D |
|---|---|---|
| Callback reached? |  |  |
| State passed? |  |  |
| Token request made? |  |  |
| Token issued? |  |  |
| OIDC response accepted? |  |  |

Explain which control protects:

~~~text
authorization response correlation
~~~

and which protects:

~~~text
OIDC ID-token/request binding
~~~

## Part 14 - Diagnose Case E

Click:

~~~text
Case E
~~~

Record:

~~~text
Callback reached?:
state_validation:
token_exchange:
OIDC validation:
local_session_created:
Browser application-session cookie present?:
~~~

The page gives you an important clue:

~~~text
OAuth succeeded
~~~

Do not call this an Okta authentication failure.

## Part 15 - Turn Case E into a login-loop diagnosis

Imagine a protected route performs:

~~~text
if local session missing:
    redirect to /login
~~~

Draw:

~~~text
App
-> Okta
-> callback
-> token success
-> OIDC success
-> no local session
-> App
-> /login again
~~~

Write:

~~~text
Last Okta/OIDC step proven successful:
First application step that fails:
~~~

## Part 16 - Complete the blind Case A-E incident notes

For each case write one short incident note using the Part 1 format.

Do not open the answer mapping yet.

Your root-cause sentence should name the exact failed object or comparison.

## Part 17 - Wrong issuer before authorization

Use the Day 7 SPA.

Start it if needed:

~~~powershell
cd scripts/day07_spa
npm install
npm run dev
~~~

Open:

~~~text
http://localhost:5173
~~~

Reset the lab configuration.

Enter an intentionally nonexistent issuer:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/not-a-real-server
~~~

Use the correct SPA client ID.

Observe Browser Console, Network, and the discovery request.

Record:

~~~text
Did /authorize start?:
Which request failed first?:
Was a user sign-in policy evaluated?:
~~~

Restore the correct issuer after evidence capture.

## Part 18 - Explain wrong issuer location

Complete:

~~~text
Configured issuer:
Discovery URL:
First failed HTTP request:
~~~

Explain why no successful discovery means you should not start by investigating MFA enrollment.

## Part 19 - App assignment and Controlled Access review

Open the Day 7 SPA or Web Application in Okta.

Record its Controlled Access model.

Answer:

~~~text
Does this app require explicit assignment?:

Is the test user directly assigned?:

Is the user assigned through a group?:

If the app allows everyone, is individual assignment required?:
~~~

Do not change anything yet.

## Part 20 - Optional assignment failure test

Only perform this if you have a disposable test user or test group.

Do not unassign your only administrator identity.

If the app requires assignments:

~~~text
1. Confirm test user can sign in.
2. Remove only that test user's applicable assignment.
3. Reproduce sign-in.
4. Capture Browser and System Log evidence.
5. Restore the assignment.
6. Prove sign-in again.
~~~

Record:

~~~text
Last successful browser step:
Okta denial evidence:
System Log outcome:
Assignment restored?:
~~~

If you do not have a safe second identity, skip the mutation and document the current Controlled Access and assignment evidence.

## Part 21 - Unexpected MFA baseline

Use the Web Application or SPA.

Record:

~~~text
Global Session Policy that applies:
App sign-in / Authentication Policy assigned to app:
Relevant rule:
Test user's enrolled authenticators:
Normal browser existing Okta session?:
~~~

Do not change policy yet.

## Part 22 - Compare existing-session vs fresh-browser behavior

Run the same application sign-in in:

~~~text
A. normal browser profile

B. fresh private/incognito window
~~~

Record:

| Evidence | Normal profile | Private window |
|---|---|---|
| Existing Okta session likely? |  |  |
| Identifier prompt? |  |  |
| Factor prompt? |  |  |
| App callback succeeds? |  |  |

Do not assume different prompts prove inconsistent policy.

The session contexts differ.


## Part 23 - Optional narrowly scoped MFA experiment

Only perform this in a safe lab tenant with a disposable test user or group.

Do not edit a broad shared default policy.

Prefer:

~~~text
dedicated test group
+
dedicated app sign-in policy
+
temporary stricter rule
~~~

Reproduce sign-in and record:

~~~text
Which policy/rule applied?:
Which factor was required?:
System Log evidence:
~~~

Restore the original app-policy assignment after the exercise.

## Part 24 - Prove MFA is not Custom Authorization Server scope policy

For the MFA case, record separately:

~~~text
Global Session Policy:
App sign-in policy:
Authorization Server Access Policy:
~~~

Explain why changing:

~~~text
employee.read
salary.read
token lifetime
~~~

does not directly solve an authentication-factor requirement.

## Part 25 - Reuse the Day 10 session app

Start:

~~~powershell
$env:OKTA_ISSUER="https://YOUR-OKTA-DOMAIN"
$env:OKTA_CLIENT_ID="YOUR-WEB-CLIENT-ID"
$env:OKTA_CLIENT_SECRET="YOUR-WEB-CLIENT-SECRET"

python scripts/python/day10_session_app.py
~~~

Open:

~~~text
http://localhost:5100
~~~

Sign in.

## Part 26 - Prove local logout vs Okta session

Click:

~~~text
Local Logout Only
~~~

Confirm the local session is gone.

Then click Sign in with Okta again.

Record:

~~~text
Local session ended?:
Browser went to Okta?:
Credentials/factor requested again?:
New local session created?:
~~~

Do not require a specific prompt result.

Policy and session context can change the user experience.

## Part 27 - Prove Okta browser-session logout is different

Use:

~~~text
Local Logout + Okta Browser Logout
~~~

Record:

~~~text
Local app session removed?:
End-session flow reached?:
Post-logout redirect returned?:
Logout state matched?:
~~~

Then compare the next sign-in behavior with Part 26.

Write which state each logout operation changed.

## Part 28 - Inspect application cookie evidence

Use the Day 10 or Day 7 server-side app.

In DevTools inspect the local session cookie.

Record only:

~~~text
cookie name:
HttpOnly:
SameSite:
Secure:
Path:
present after login?:
present after local logout?:
~~~

Do not record the cookie value.

## Part 29 - Separate browser-cookie vs server-session evidence

For a healthy server-side request, prove both:

~~~text
Browser sends local session cookie
~~~

and:

~~~text
Server recognizes session
~~~

Answer:

~~~text
If browser never sends cookie, which side do you inspect first?:

If browser sends cookie but server says no session, which side do you inspect first?:
~~~

## Part 30 - Start the local CORS evidence harness

Stop anything using ports 5400 or 5401.

Clear:

~~~powershell
Remove-Item Env:DAY13_CORS_ALLOW_ORIGIN -ErrorAction SilentlyContinue
~~~

Run:

~~~powershell
python scripts/python/day13_cors_lab.py
~~~

Open:

~~~text
http://localhost:5400
~~~

Open Network and Console.

## Part 31 - Reproduce browser CORS failure

Click:

~~~text
Call API from browser
~~~

The page origin is:

~~~text
http://localhost:5400
~~~

The API origin is:

~~~text
http://localhost:5401
~~~

Record:

~~~text
OPTIONS request present?:
OPTIONS status:
Access-Control-Allow-Origin present?:
Did browser send GET /data?:
Console message:
~~~

Do not call this an OAuth failure.

## Part 32 - Prove the API itself works outside browser CORS

With the same CORS harness running, use Postman or curl:

~~~powershell
curl.exe -H "Authorization: Bearer demo-token" http://localhost:5401/data
~~~

Expected server response:

~~~text
200
server_received_request = true
~~~

Record:

~~~text
Postman/curl result:
Browser result:
~~~

Explain why both results can be true at the same time.

## Part 33 - Fix only the CORS owner

Stop the CORS harness.

Set:

~~~powershell
$env:DAY13_CORS_ALLOW_ORIGIN="http://localhost:5400"
~~~

Restart:

~~~powershell
python scripts/python/day13_cors_lab.py
~~~

Repeat the browser call.

Record:

~~~text
OPTIONS allowed?:
GET sent?:
GET HTTP:
Browser fetch succeeded?:
~~~

The fix was made on the API at localhost:5401, not in Okta Trusted Origins.

## Part 34 - Explain Okta Trusted Origins correctly

Complete:

~~~text
SPA calls my own API cross-origin:
CORS configured on __________________

Browser JavaScript calls supported Okta API using Okta session cookie:
Trusted Origin may be __________________

Browser calls supported Okta API using OAuth bearer token:
Trusted Origin is not required merely for __________________
~~~

Do not reduce the answer to:

> Add Trusted Origin when browser fails.

## Part 35 - Preflight proof

From the successful CORS test, inspect:

~~~text
OPTIONS /data
~~~

and:

~~~text
GET /data
~~~

Record:

~~~text
Which came first?:
Which response headers allowed the browser to proceed?:
~~~

Then compare with the failed test.

Write:

> In the failed case, did the real GET leave the browser?

## Part 36 - Wrong client ID in SPA

Reset the Day 7 SPA configuration.

Use:

~~~text
Correct issuer
Wrong client ID
~~~

Try Sign in.

Record:

~~~text
Browser reached Okta?:
Authorization request accepted?:
Callback reached SPA?:
Tokens stored?:
Error evidence:
~~~

Restore the real client ID.

## Part 37 - Compare wrong issuer vs wrong client ID

Fill:

| Evidence | Wrong issuer | Wrong client ID |
|---|---|---|
| Discovery succeeds? |  |  |
| /authorize reached? |  |  |
| Okta can identify client? |  |  |
| Callback reached? |  |  |

Do not use the same root-cause sentence for both.

## Part 38 - Build a dev-vs-prod comparison without guessing

Create a table for your intended dev/prod design.

| Setting | Dev | Prod | Same intentionally? |
|---|---|---|---|
| Issuer |  |  |  |
| Client ID |  |  |  |
| App type |  |  |  |
| Redirect URI |  |  |  |
| Sign-out URI |  |  |  |
| Browser origin |  |  |  |
| HTTPS |  |  |  |
| Cookie settings |  |  |  |
| App sign-in policy |  |  |  |
| Controlled Access |  |  |  |
| Assignment |  |  |  |

For every difference write:

~~~text
intentional
or
possible defect
~~~

## Part 39 - System Log correlation exercise

Run one healthy sign-in and one failing hidden case.

In System Log, correlate by:

~~~text
time
user
application
transaction.id
externalSessionId
rootSessionId when available
~~~

Answer:

~~~text
Which events belong to Okta?:

Which failed application step is invisible to Okta?:
~~~

Example:

~~~text
Okta can show successful SSO
while
your application can still fail local session creation
~~~

## Part 40 - Write three production-quality incident notes

Choose any three failures from:

~~~text
Case A-E
wrong issuer
assignment
MFA policy
local logout / SSO
CORS
wrong SPA client ID
~~~

Each note must contain:

~~~text
Observed symptom
Last confirmed successful step
First failed step
Evidence
Root cause
Single change
Proof after change
~~~

Do not write:

> Changed a few settings and it worked.

## Part 41 - Diagnose from symptoms only

Without looking at previous answers, classify the first area to inspect.

### Symptom A

~~~text
Browser never makes a request to Okta.
Console shows SDK initialization error.
~~~

### Symptom B

~~~text
/authorize appears in Network.
No callback ever reaches the app.
~~~

### Symptom C

~~~text
Callback reaches app.
Backend says state validation failed.
No /token request is made.
~~~

### Symptom D

~~~text
/token succeeds.
ID token validation succeeds.
Browser never retains local app session.
~~~

### Symptom E

~~~text
Postman API call succeeds.
Browser sends OPTIONS.
Protected GET never follows.
~~~

### Symptom F

~~~text
User signs in.
System Log shows SSO success.
Application immediately starts sign-in again.
~~~

Write the first investigation layer for each.

## Part 42 - Complete the browser troubleshooting matrix

| Failure | Browser reached Okta? | Callback reached app? | Token request? | Local app state? | First layer |
|---|---:|---:|---:|---:|---|
| Redirect mismatch |  |  |  |  |  |
| Lost transaction |  |  |  |  |  |
| State mismatch |  |  |  |  |  |
| Nonce mismatch |  |  |  |  |  |
| Local session skipped |  |  |  |  |  |
| Wrong nonexistent issuer |  |  |  |  |  |
| CORS preflight denied | N/A | N/A | N/A | N/A |  |

Fill from actual evidence.

## Part 43 - Blind-case self-check

Only open this after you have completed incident notes for A through E.

<details>
<summary>Case mapping and expected failed layer</summary>

### Case A

~~~text
Unregistered redirect URI
~~~

Expected evidence:

~~~text
Browser reaches Okta authorization endpoint.
Requested redirect URI is not the registered normal callback.
Normal callback does not receive an authorization code.
~~~

### Case B

~~~text
Pending transaction missing
~~~

Expected evidence:

~~~text
Callback reaches the app.
Transaction cookie can exist.
Server-side pending transaction record is absent.
Token request is not attempted.
~~~

### Case C

~~~text
State mismatch
~~~

Expected evidence:

~~~text
Pending transaction exists.
Returned state does not match expected state.
Token request is not attempted.
~~~

### Case D

~~~text
Nonce mismatch
~~~

Expected evidence:

~~~text
State passes.
Token exchange succeeds.
ID-token/OIDC validation fails on nonce.
~~~

### Case E

~~~text
Local application session intentionally not created
~~~

Expected evidence:

~~~text
State passes.
Token exchange succeeds.
OIDC validation succeeds.
Local session creation is skipped.
~~~

</details>

## Part 44 - Final explain-back

Explain this without looking:

~~~text
I do not troubleshoot login failed as one event.

I follow the redirect transaction and identify the last step I can prove succeeded.

Browser Network tells me what the browser actually requested and received.

Application logs tell me what the app did with the callback, token exchange, and local session.

Okta System Log tells me what Okta evaluated for authentication, app access, policy, and session events.

A redirect mismatch occurs before the callback.

State failure occurs after the callback but before token exchange.

Nonce failure occurs after token exchange during OIDC validation.

Successful Okta authentication does not prove my application created its own session.

Postman success does not prove a browser path because browsers add origin, CORS, cookie, storage, and JavaScript behavior.

Trusted Origins are not a universal CORS fix.

For unexpected MFA I inspect Global Session Policy and the app sign-in policy before changing API access policy.

I change one relevant control, repeat the same transaction, and prove the result changed for the reason I expected.
~~~

## Day 13 completion check

You are ready for Day 14 when you can diagnose browser and authentication failures without being told the category and can produce an incident note containing:

~~~text
last successful step
first failed step
evidence
root cause
one change
proof
~~~

Do not move on if your troubleshooting still begins with random configuration changes.
