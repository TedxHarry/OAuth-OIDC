# Day 6 Lab - Compare SPA and Web Client Authentication

## Purpose

Days 3 to 5 used a public SPA client.

Today you create a confidential Web Application and compare the two registrations side by side.

Then you run Authorization Code + PKCE with the Web Application and add client authentication at the token endpoint.

Complete the lesson first:

[Day 6 - Okta App Types and Client Authentication](../lessons/day-06-app-types-client-auth.md)

## Safety rule

Do not place the Web Application client secret into:

~~~text
GitHub
browser JavaScript
screenshots
chat
tickets
shared notes
~~~

Keep it only in your local lab environment.

## Part 1 - Record the existing SPA

Open the Day 3 SPA integration.

Record safe configuration values:

~~~text
Application type:
Client ID:
Client authentication:
Authorization Code enabled?:
Refresh Token enabled?:
Sign-in redirect URI:
~~~

Expected client-authentication classification:

~~~text
none
~~~

## Part 2 - Create a Web Application

In Okta Admin Console:

~~~text
Applications and Resources
        |
        v
Applications
        |
        v
Create App Integration
~~~

Choose:

~~~text
Sign-in method:
OIDC - OpenID Connect

Application type:
Web Application
~~~

Name:

~~~text
OAuth OIDC Day 6 Web Client Lab
~~~

Keep Authorization Code enabled.

Use:

~~~text
http://localhost:8000/callback
~~~

as the sign-in redirect URI.

Assign the same test user or test group used in earlier labs.

Save.

## Part 3 - Compare the registrations

Open the Web Application General page.

Locate:

~~~text
Client ID
Client Secret
~~~

Compare:

| Setting | Day 3 SPA | Day 6 Web Application |
|---|---|---|
| Runs where | Browser | Controlled backend |
| Public or confidential | Public | Confidential |
| Client ID | Yes | Yes |
| Protected client secret | No | Yes |
| Authorization Code | Yes | Yes |
| PKCE usable | Yes | Yes |
| Client authentication at token endpoint | none | Secret-based in this lab |

Explain why the difference exists.

Correct reasoning:

> The backend can protect a client credential from the end user.

## Part 4 - Start the callback server

Stop anything using port 8000, then run:

~~~powershell
python scripts/python/day03_pkce_callback_server.py
~~~

## Part 5 - Prepare PKCE values for the Web client

Run on one line:

~~~powershell
python scripts/python/day03_prepare_authorization.py --okta-domain https://YOUR-OKTA-DOMAIN --client-id YOUR-WEB-CLIENT-ID
~~~

Keep state, nonce, code_verifier, and authorization URL private on your machine.

## Part 6 - Run the authorization request

Open the generated authorization URL in a private browser.

Complete authentication.

At the callback:

~~~text
verify returned state
copy the fresh authorization code locally
~~~

The presence of a client secret did not remove PKCE from this transaction.

## Part 7 - Build the confidential token request

Create:

~~~text
POST https://YOUR-OKTA-DOMAIN/oauth2/v1/token
~~~

In Postman Authorization choose:

~~~text
Basic Auth
~~~

Use:

~~~text
Username = Web Application Client ID
Password = Web Application Client Secret
~~~

Body type:

~~~text
x-www-form-urlencoded
~~~

Body:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| redirect_uri | http://localhost:8000/callback |
| code | Fresh authorization code |
| code_verifier | Original verifier |

Do not place the client secret in the form body for this test.

## Part 8 - Inspect the request

Use Postman Console if needed.

Identify:

~~~text
Authorization header:
Basic ...

Content-Type:
application/x-www-form-urlencoded

Body:
grant_type
redirect_uri
code
code_verifier
~~~

Explain:

~~~text
Basic Authorization header
-> client authentication

code_verifier
-> PKCE proof
~~~

## Part 9 - Send the successful request

Send it.

Record only safe observations:

~~~text
HTTP status:
token response returned?:
client authentication method:
PKCE used?:
~~~

## Part 10 - Break client authentication

Start a fresh authorization transaction and obtain a fresh code.

Use the correct verifier.

In Postman Basic Auth use:

~~~text
Username:
correct Web Client ID

Password:
intentionally wrong client secret
~~~

Send.

Record the actual OAuth error returned by your tenant.

Reason from evidence:

~~~text
/authorize succeeded
user authentication succeeded
callback succeeded
PKCE verifier is correct
/token failed
client credential is wrong
~~~

This is a client-authentication failure.

## Part 11 - Break PKCE separately

Start another fresh transaction.

Use:

~~~text
correct client ID
correct client secret
wrong code_verifier
~~~

Send the token request.

Record the actual error.

Reason:

~~~text
client authentication can succeed
but
PKCE validation can still fail
~~~

The two checks are separate.

## Part 12 - Compare results

| Test | Client credential | PKCE verifier | Result |
|---|---|---|---|
| Success | Correct | Correct |  |
| Wrong secret | Wrong | Correct |  |
| Wrong verifier | Correct | Wrong |  |

For each failure:

~~~text
Last successful step:
First failed step:
Evidence:
Root cause:
~~~

## Part 13 - Recognize other auth methods

Complete:

| Method | Proof sent by client | Public client suitable? |
|---|---|---|
| none | No protected credential | Yes |
| client_secret_basic | Shared secret in Basic Authorization header | No |
| client_secret_post | Shared secret in form body | No |
| client_secret_jwt | JWT signed with shared secret | No |
| private_key_jwt | JWT signed with private key | No |

You will implement private_key_jwt later.

## Part 14 - Architecture classification

Classify each:

### A
React SPA running entirely in browser.

### B
Python Flask backend that owns OIDC callback and stores credentials server-side.

### C
iOS native application.

### D
Employee API that only receives bearer access tokens.

### E
Scheduled service that obtains tokens to call Okta APIs.

For each:

~~~text
OAuth client?
Public or confidential?
Likely Okta app type or pattern?
Can it protect a client secret?
~~~

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### SPA

Public client. It cannot protect a client secret.

### Web Application

Confidential client. Its backend can protect credentials.

### Wrong secret

Correct PKCE does not fix invalid client authentication.

### Wrong verifier

Correct client authentication does not fix invalid PKCE.

### Employee API

If it only receives and validates access tokens, it is a resource server, not an OAuth client in that role.

### API Service

It represents a service client. It is not another name for every custom API.

</details>

## Day 6 completion check

You are ready for Day 7 when you can explain:

~~~text
Why app type follows runtime architecture
Why SPA is public
Why Web Application is confidential
Why client ID is not client authentication
How client_secret_basic works
Why PKCE and client auth are separate
Why a resource server is not automatically an API Service client
~~~
