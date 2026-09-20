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
