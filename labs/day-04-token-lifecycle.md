# Day 4 Lab - Inspect Tokens and Refresh Them

## Purpose

This lab continues directly from Day 3.

You will obtain:

~~~text
ID token
Access token
Refresh token
~~~

Then you will prove which component each token is for and use the refresh token to obtain a new token response.

Complete the lesson first:

[Day 4 - ID Tokens, Access Tokens, and Refresh Tokens](../lessons/day-04-tokens-and-refresh.md)

## Safety rule

Do not commit or paste these live values into GitHub, chat, tickets, or screenshots:

~~~text
authorization code
access token
ID token
refresh token
code_verifier
~~~

Record observations, not live credentials.

## Part 1 - Reuse the Day 3 SPA application

Use the SPA app integration created in Day 3.

You should still have:

~~~text
Application type:
Single-Page Application

Sign-in redirect URI:
http://localhost:8000/callback

Client authentication:
None
~~~

## Part 2 - Enable Refresh Token grant

In the Okta Admin Console, open the Day 3 SPA app integration.

Edit the General settings.

Keep:

~~~text
Authorization Code
~~~

and enable:

~~~text
Refresh Token
~~~

Save.

For SPA integrations, Okta uses rotating refresh-token behavior by default when Refresh Token is enabled.

Do not change the rotation settings for this lab unless you already have a deliberate test configuration.

## Part 3 - Start the callback server

If it is not already running:

~~~bash
python scripts/python/day03_pkce_callback_server.py
~~~

The callback is:

~~~text
http://localhost:8000/callback
~~~

## Part 4 - Prepare authorization with offline_access

Run:

~~~bash
python scripts/python/day03_prepare_authorization.py \
  --okta-domain https://YOUR-OKTA-DOMAIN \
  --client-id YOUR-CLIENT-ID \
  --scope "openid profile email offline_access"
~~~

Confirm the authorization request includes:

~~~text
offline_access
~~~

Keep the generated state, nonce, and verifier for this transaction.

## Part 5 - Complete Authorization Code with PKCE

Open the generated authorization URL.

Complete sign-in if required.

At the callback:

1. confirm a code was returned
2. compare returned state with expected state

If state does not match, stop.

## Part 6 - Exchange the code in Postman

Use the Day 3 token request.

~~~text
POST https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Body:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| client_id | Your SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| code | Fresh authorization code |
| code_verifier | Verifier from this transaction |

Send the request.

## Part 7 - Identify the response fields

Do not copy the live token strings into your notes.

Record whether each field is present.

| Response field | Present? | Consumer |
|---|---|---|
| id_token |  | Client application |
| access_token |  | Client receives it, then presents it to the intended resource server. In this Org-AS lab, the intended resource server is Okta |
| refresh_token |  | Client receives and stores it, then later presents it to the authorization server token endpoint |
| expires_in |  | Access-token lifetime in seconds |
| scope |  | Scopes associated with response |

If refresh_token is not present, check:

~~~text
Refresh Token grant enabled?
offline_access requested at /authorize?
correct app integration?
fresh authorization transaction after configuration change?
~~~

## Part 8 - Inspect the ID token

Run:

~~~bash
python scripts/python/day04_decode_id_token.py
~~~

Paste the ID token when prompted.

The script displays the decoded header and payload.

Important:

~~~text
This is inspection only.
It is NOT validation.
~~~

Find:

~~~text
iss
sub
aud
iat
exp
nonce
email, if returned
~~~

## Part 9 - Connect the claims to the flow

Answer:

### aud

Does the ID token audience correspond to your client?

### nonce

Does the decoded nonce match the nonce generated before /authorize?

### iat

When was the token issued?

### exp

When does it expire?

### iss

Which authorization server issued it?

Do not conclude the token is trusted simply because these values look correct.

Day 5 performs validation.

## Part 10 - Respect the org-AS access-token boundary

Do not build logic around the access token's internal claims.

Also do not send this Org-AS access token to our future Employee API.

Record this rule:

~~~text
Current Day 4 access token:
issued by Okta org authorization server

Intended consumer:
Okta

Our own future Employee API:
will use a Custom Authorization Server later
~~~

## Part 11 - Use the refresh token

Create another Postman request.

Method:

~~~text
POST
~~~

URL:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

Headers:

~~~http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
~~~

Body:

| Key | Value |
|---|---|
| grant_type | refresh_token |
| client_id | Your SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| scope | openid profile email offline_access |
| refresh_token | Refresh token from the previous response |

Do not use a client secret.

Send the request.

## Part 12 - Compare the refresh response

Record only safe observations:

~~~text
HTTP status:
new access_token present?:
new id_token present?:
refresh_token field present?:
expires_in:
scope:
~~~

If a replacement refresh token is returned, a real client must update its stored refresh-token state.

The exact replacement and reuse behavior depends on the refresh-token settings.

## Part 13 - Inspect the new ID token if returned

Run the decoder again.

Compare:

~~~text
iss
sub
aud
iat
exp
~~~

Ask:

> Which values describe the same identity and client relationship, and which changed because this is a newly issued token?

## Part 14 - Prove offline_access matters

Start another fresh authorization transaction without offline_access:

~~~bash
python scripts/python/day03_prepare_authorization.py \
  --okta-domain https://YOUR-OKTA-DOMAIN \
  --client-id YOUR-CLIENT-ID \
  --scope "openid profile email"
~~~

Complete authorization and code exchange.

Compare the response with the transaction that requested offline_access.

Record:

~~~text
offline_access requested?
refresh_token returned?
~~~

The Refresh Token grant being enabled does not mean every authorization-code response contains a refresh token.

## Part 15 - Use an invalid refresh token

Change the Postman refresh_token field to:

~~~text
not-a-real-refresh-token
~~~

Send the request.

Record:

~~~text
HTTP status:
OAuth error:
error description:
~~~

Then answer:

1. Did a browser sign-in happen?
2. Did this request go to /authorize?
3. Which endpoint rejected the request?
4. Which credential was invalid?

This is a refresh-token processing failure at /token.

It is not a user-authentication failure.

## Part 16 - Explain the delivery path before drawing it

In your own words explain:

```text
Who receives all three tokens from /token?
Who consumes the ID token?
Who receives the access token later?
Where does the refresh token go later?
```

Correct working logic:

```text
Okta returns tokens to client
Client consumes ID token
Client presents access token to intended resource server
Client later presents refresh token back to Okta /token
```

## Part 17 - Draw the lifecycle

Without looking at the diagram, draw:

~~~text
Authorization Code + PKCE
        |
        v
ID + access + refresh
        |
        v
access token lifetime
        |
        v
refresh token -> /token
        |
        v
new token response
~~~

Label the consumer for all three token types.

Compare with:

[Day 4 flow diagrams](../diagrams/day-04-token-lifecycle.md)

## Part 18 - Correlate refresh activity with Okta System Log

After one successful refresh request and the deliberately invalid refresh-token request, open the Okta System Log.

Use:

```text
time of request
Day 3/Day 4 application
client ID when available
OAuth/OIDC event category
outcome
```

to correlate what Okta recorded.

Do not replace the HTTP evidence with the System Log.

Use them together:

```text
Postman request and response
        +
token-flow reasoning
        +
Okta System Log
```

If the System Log does not expose the exact detail you expected, record only what it actually shows.

## Part 19 - Evidence record

Record:

~~~text
SPA client ID:
Authorization server type:
Refresh Token grant enabled?:

Authorization request:
offline_access present?:

First token response:
ID token present?:
access token present?:
refresh token present?:
expires_in:

ID token inspection:
iss:
aud:
nonce matched?:
iat:
exp:

Refresh request:
endpoint:
grant_type:
client secret used?:
HTTP status:

Refresh response:
new access token present?:
new ID token present?:
replacement refresh token present?:
~~~

Do not record live token strings.

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Token consumers

~~~text
ID token
-> client application

Access token
-> intended resource server

Refresh token
-> authorization server /token endpoint
~~~

### offline_access

For Authorization Code flow, offline_access must be requested at /authorize to request refresh-token capability.

The Okta app must also allow the Refresh Token grant.

### ID token decoding

Decoding makes claims readable.

It does not verify the signature, issuer, audience, expiration, or nonce.

### Org authorization server access token

The Day 4 access token comes from the org authorization server.

Okta, not our future custom Employee API, is the intended consumer.

### Refresh

A valid refresh token can obtain new tokens without another interactive authorization flow.

A refresh-token failure occurs at /token, not at the original user authentication step.

</details>

## Day 4 completion check

You are ready for Day 5 when you can explain:

~~~text
ID token -> client
Access token -> resource server
Refresh token -> authorization server

Why the three tokens are not interchangeable
Why offline_access is required
Why a refresh token is sensitive
Why decoding is not validation
Why our org-AS access token is not for our own API
What changes when a refresh request succeeds
~~~
