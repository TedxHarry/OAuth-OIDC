## Day 2 — Read the HTTP transaction before changing settings

### The reason this day matters

Many OAuth tickets sound vague:

> Login is not working.

That description is almost useless. A login is a sequence of HTTP transactions. Your job is to find the **last transaction that succeeded** and the **first one that failed**.

Start thinking in requests, not screens.

### Front channel: the browser carries the transaction

A typical browser authorization begins like this:

```text
Browser
   |
   | GET /authorize?...parameters...
   v
Okta
```

After authentication/authorization, Okta does not normally POST tokens directly into your application through the browser. It redirects the browser:

```text
Okta
   |
   | HTTP 302
   | Location: https://app.example.com/callback?code=ABC&state=XYZ
   v
Browser
   |
   | GET /callback?code=ABC&state=XYZ
   v
Application
```

The browser is carrying the authorization response back to the application's callback.

### Back channel: direct communication

For a server-side web application, the code exchange usually happens directly from the backend to Okta:

```text
Application backend
       |
       | POST /token
       v
      Okta
       |
       | token response
       v
Application backend
```

The user does not need to see this HTTP exchange.

A SPA is different: the browser-based client can perform the token exchange itself using PKCE, without a client secret.

### Learn the pieces of a request

A request is not just a URL. You need to be comfortable checking:

```text
Method
URL
Query parameters
Request headers
Request body
Cookies
Response status
Response headers
Response body
Redirect Location
```

For example, an authorization request may look conceptually like:

```http
GET /oauth2/default/v1/authorize?
  client_id=0oa...
  &response_type=code
  &redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback
  &scope=openid%20profile
  &state=...
  &nonce=...
  &code_challenge=...
  &code_challenge_method=S256
```

You do not need to memorize the full URL. You need to be able to look at it and ask whether the values make sense.

### Status codes are clues, not final diagnoses

Use them as direction:

```text
302
→ redirect is happening; often normal in browser flow

400 from /authorize or /token
→ request/configuration/grant/client problem

401 from protected API
→ the API does not accept the authentication credential/token

403 from protected API
→ the token/caller is accepted, but permission is insufficient
```

Frameworks may vary, so do not turn that into a rigid law. It is your first branch in the investigation.

### Cookies: understand what they represent

When the browser has an Okta session cookie, Okta may already know the user is signed in. That is why a user can be redirected to Okta and immediately come back without typing credentials again.

That cookie is not the same thing as:

```text
ID token
Access token
Refresh token
Application session cookie
```

You will separate those more deeply on Day 10.

### CORS: know when it can and cannot be the problem

CORS is enforced by browsers.

Therefore:

```text
Postman works
curl works
browser fails
```

can reasonably send you toward:

```text
CORS
Trusted Origins
browser origin
cookies
callback behavior
```

But if a server-to-server curl request is failing, “CORS” is not a useful diagnosis.

### Your lab today

Open Chrome/Edge DevTools → Network.

Perform one Okta login and trace:

1. The application's initial login action.
2. The request to Okta `/authorize`.
3. Any authentication-related redirects.
4. The callback to the application.
5. The authorization `code` in the callback.
6. Any visible token request if this is a SPA.
7. The application's API call.

Write down:

```text
request URL
method
status
important parameters
who made the request
what the next hop was
```

### Break/fix

Change the callback route in the application request so it no longer matches the registered redirect URI.

Do not immediately fix it. First prove:

```text
Did the browser reach Okta?
Did user authentication happen?
Did Okta reject before returning a code?
What exact redirect URI was requested?
What is registered in Okta?
What does System Log show?
```

### Explain-back checkpoint

You should be able to say:

> OAuth troubleshooting is transaction troubleshooting. I first locate the last successful HTTP step. Browser redirects are front channel; token/API calls may be back channel. Once I know which component made the failed request, the possible causes become much smaller.

---
