# Day 3 Lab - Run Authorization Code with PKCE against Okta

## Purpose

This is the first lab where you run a real OAuth/OIDC authorization flow against your Okta tenant.

You will use:

- your Okta integration tenant
- Chrome or Edge
- Python
- Postman
- the course repository

Complete the lesson first:

[Day 3 - Authorization Code with PKCE](../lessons/day-03-authorization-code-pkce.md)

## What you will prove

By the end of the lab, you will have evidence for this flow:

```text
Client creates verifier and challenge
        |
        v
Browser sends challenge to /authorize
        |
        v
User authenticates with Okta
        |
        v
Browser receives authorization code
        |
        v
Client checks state
        |
        v
Postman sends code + verifier to /token
        |
        v
Okta verifies PKCE
        |
        v
Tokens returned
```

Then you will deliberately break code redemption and prove why it fails.

## Training architecture warning

This lab splits one logical OAuth client across several tools so that you can see every step:

```text
Python
-> generates transaction values

Browser
-> carries the front-channel authorization request and callback

Python callback server
-> receives the callback

Postman
-> manually performs the token request
```

A real SPA does not ask a human to copy the authorization code and verifier into Postman.

In production, the SPA or its OAuth/OIDC library performs those steps as one client implementation.

## Important lab boundary

For Day 3, use the **Okta org authorization server**.

Endpoints:

```text
Authorize:
https://{yourOktaDomain}/oauth2/v1/authorize

Token:
https://{yourOktaDomain}/oauth2/v1/token
```

We are using it because today's goal is the Authorization Code + PKCE transaction itself.

We are not using today's access token to protect our own custom API.

Custom Authorization Servers, custom scopes, audience, and access policies are taught later.

## Part 1 - Stop the Day 2 server

If the Day 2 Python server is still running on port 8000, stop it with:

```text
Ctrl+C
```

Day 3 uses the same local port for the callback.

## Part 2 - Create the Okta SPA app integration

In the Okta Admin Console:

```text
Applications
  |
  v
Applications
  |
  v
Create App Integration
```

Depending on the Admin Console version, the navigation may appear as:

```text
Applications and Resources
  |
  v
Applications
```

Choose:

```text
Sign-in method:
OIDC - OpenID Connect

Application type:
Single-Page Application
```

Use an app name such as:

```text
OAuth OIDC Day 3 PKCE Lab
```

For Grant type, keep:

```text
Authorization Code
```

You do not need Refresh Token for today's lab.

Set the Sign-in redirect URI to:

```text
http://localhost:8000/callback
```

For Controlled access, either:

- assign the specific test user you will use, or
- allow the appropriate users in your integration tenant

Save the integration.

## Part 3 - Record the Client ID

Open the app integration's General page.

Find:

```text
Client ID
```

Copy it to a local text editor.

The client ID is not a client secret.

For a SPA integration, the client authentication method should be:

```text
None
```

The browser application is a public client.

Do not create or place a client secret into this lab flow.

## Part 4 - Start the local callback server

From the repository root:

```bash
python scripts/python/day03_pkce_callback_server.py
```

You should see:

```text
Day 3 callback server running on http://localhost:8000
Registered redirect URI should be:
http://localhost:8000/callback
```

Leave this terminal running.

## Part 5 - Prepare a PKCE transaction

Open a second terminal.

Run:

```bash
python scripts/python/day03_prepare_authorization.py \
  --okta-domain https://YOUR-OKTA-DOMAIN \
  --client-id YOUR-CLIENT-ID
```

Example domain shape:

```text
https://integrator-123456.okta.com
```

Do not use the Admin Console URL with `-admin`.

Use your actual Okta org domain.

The script prints:

```text
state
nonce
code_verifier
code_challenge
code_challenge_method
authorization URL
token endpoint
```

Keep this terminal open.

Do not share the verifier.

## Part 6 - Before opening the URL, identify each value

From the generated authorization URL, locate:

```text
client_id
response_type
scope
redirect_uri
state
nonce
code_challenge
code_challenge_method
```

For each one, say what it does.

For `scope`, specifically explain:

```text
openid
-> request OIDC authentication and an ID token

profile
-> request standard profile claims

email
-> request standard email claims
```

Do not continue until you can explain why the verifier is not present in the authorization URL.

## Part 7 - Open DevTools

Open a private or incognito browser window.

Open DevTools and select:

```text
Network
```

Enable:

```text
Preserve log
```

This makes it easier to follow redirects.

## Part 8 - Run /authorize

Copy the authorization URL printed by the Python script into the private browser.

You should be sent to Okta.

If there is no existing Okta browser session, authenticate using the test user assigned to the application.

After the authorization step, Okta redirects the browser to:

```text
http://localhost:8000/callback
```

The callback page should display:

```text
Returned state
Authorization code
```

Do not share the authorization code.

## Part 9 - Prove the front-channel transaction

In DevTools, locate the request to the Okta authorization endpoint.

Record locally:

```text
Method:
Authorization endpoint:
client_id:
response_type:
redirect_uri:
scope:
state:
nonce:
code_challenge:
code_challenge_method:
```

Then locate the callback request.

Record:

```text
Callback URL:
code present?:
state returned:
```

Now compare:

```text
state generated before /authorize
vs
state returned to /callback
```

They must match.

This is the client-side state check.

## Part 10 - Build the /token request in Postman

Create a new Postman request.

Method:

```text
POST
```

URL:

```text
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
```

Headers:

```http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
```

Under Body, choose:

```text
x-www-form-urlencoded
```

Add:

| Key | Value |
|---|---|
| `grant_type` | `authorization_code` |
| `client_id` | Your SPA client ID |
| `redirect_uri` | `http://localhost:8000/callback` |
| `code` | The authorization code from the callback |
| `code_verifier` | The original verifier from the Python script |

Do not add a client secret.

Do not use Basic Auth.

## Part 11 - Send the successful token request

Send the Postman request.

If the transaction is valid, the response should contain values such as:

```text
access_token
token_type
expires_in
scope
id_token
```

Do not paste live tokens into chat or tickets.

For Day 3, do not spend time decoding every token claim.

Day 4 teaches the token types and lifecycle.

Today, prove:

```text
/authorize succeeded
state matched
code was returned
/token received code + verifier
PKCE passed
tokens were issued
```

## Part 12 - Draw what just happened

Without looking at the lesson, draw:

```text
Client
Browser
Okta /authorize
Callback
Okta /token
```

Label:

- challenge
- code
- state
- verifier
- token response

Compare your drawing with:

[Day 3 flow diagrams](../diagrams/day-03-authorization-code-pkce.md)

## Part 13 - Break PKCE with the wrong verifier

Start a **new authorization transaction**.

Run the preparation script again so you have:

```text
new state
new nonce
new verifier
new challenge
new authorization URL
```

Open the new authorization URL and obtain a fresh authorization code.

In Postman, use the fresh code but intentionally send:

```text
code_verifier=wrong-verifier-value-that-does-not-match
```

Send the request.

Expected result:

```text
Token request rejected
```

Okta commonly reports an OAuth `invalid_grant` error for an invalid code redemption condition. Record the actual response your tenant returns.

Now diagnose it:

```text
Did /authorize succeed?
Did the browser reach the callback?
Was an authorization code returned?
Did /token succeed?
Which PKCE value was wrong?
```

The failure is at:

```text
code redemption / PKCE verification
```

not user authentication.

## Part 14 - Prove authorization codes are single-use

Start another fresh transaction.

This time:

1. obtain a fresh authorization code
2. exchange it successfully using the correct verifier
3. keep the same Postman request
4. send the exact same token request again

The second redemption should be rejected because the authorization code has already been consumed.

Record:

```text
First exchange status:
Second exchange status:
Second response error:
```

Explain:

> Why should a successfully redeemed authorization code not be usable again?

## Part 15 - State mismatch thought test

Do not change anything in Okta.

Look at:

```text
expected state
returned state
```

Now imagine your application had stored:

```text
expected state = AAA
```

but received:

```text
returned state = BBB
```

Who should reject the transaction?

Answer:

```text
The client application
```

Okta's job is to return the state value from the authorization request.

The client must compare it with the value it expected.

Do not send the code to `/token` when state validation fails.

## Part 16 - Evidence record

For your successful transaction, record:

```text
Okta domain:
Client type:
Client authentication:
Authorization endpoint:
Token endpoint:
Redirect URI:

Generated:
state
nonce
code_verifier
code_challenge

Browser authorization:
Did /authorize load?
Did user authentication complete?
Did callback occur?
Did returned state match?

Token exchange:
Did /token succeed?
Was a client secret used?
Were tokens returned?
```

Do not store live tokens or authorization codes in the repository.

## Part 17 - Failure record

For each deliberate failure, use:

```text
Scenario:
Last successful step:
First failed step:
HTTP status:
OAuth error:
Evidence:
Root cause:
Why the previous step was not the problem:
```

Complete this for:

1. wrong code verifier
2. reused authorization code

## Part 18 - Correlate with Okta System Log

After the successful transaction and at least one failed token request, open the Okta System Log.

Use the approximate time and the Day 3 client/application to locate relevant OAuth/OIDC activity.

The exact event details can vary, so do not force the System Log to say what you expect.

Instead compare:

```text
successful transaction time
failed transaction time
client/app involved
outcome
available debug or failure details
```

Your primary evidence for the PKCE failure is still the actual `/token` request and response.

The System Log is supporting server-side evidence.

This is the troubleshooting habit we will keep using:

```text
Browser or Postman evidence
        +
token/request evidence
        +
Okta System Log when useful
```

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Successful flow

The client creates the verifier first.

The client derives the challenge from the verifier.

The authorization request sends the challenge, not the verifier.

Okta returns an authorization code through the browser callback.

The client checks state.

The token request sends the code and original verifier.

Okta derives the expected challenge from the verifier and compares it with the challenge associated with the authorization request.

If the transaction is valid, tokens are returned.

### Wrong verifier

The browser authorization can succeed.

The user can authenticate successfully.

The callback can contain a valid authorization code.

The token exchange still fails because the verifier does not match the challenge associated with the authorization transaction.

Therefore:

```text
authentication success
does not mean
token exchange success
```

### Reused code

A successful authorization-code exchange consumes the code.

Sending the same code again must not create another valid token exchange.

### State

State is checked by the client.

A state mismatch means the client should stop before code redemption.

</details>

## Day 3 completion check

You are ready for Day 4 when you can explain the flow without reading:

```text
Why an authorization code exists
Why the SPA has no client secret
How verifier becomes challenge
What goes to /authorize
What comes back to callback
Who checks state
What goes to /token
What Okta checks for PKCE
Why the code is single-use
Why a wrong verifier fails after authentication succeeded
```

## Official references

- [Okta: Authorization Code with PKCE](https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/)
- [Okta: Create an app integration](https://developer.okta.com/docs/guides/create-an-app-integration/-/main/)
