## Day 7 — Implement a web app and a SPA, then compare where trust lives

### Why implement both

If you only learn one architecture, you may apply its rules to the wrong runtime.

A server-side web application and a SPA can both use Authorization Code + PKCE, but token handling and client authentication differ.

### Server-side web app

Conceptual flow:

```text
Browser
   |
   | redirect to Okta
   v
Okta
   |
   | callback with code
   v
Browser -> Web backend callback
              |
              | POST /token
              | client authentication + code_verifier
              v
             Okta
              |
              | tokens
              v
          Web backend
              |
              | creates application session cookie
              v
            Browser
```

The browser may end up holding only the application's session cookie while OAuth tokens remain on the backend.

That can reduce exposure of OAuth tokens to browser JavaScript.

### SPA

```text
Browser SPA
   |
   | /authorize + PKCE
   v
Okta
   |
   | callback with code
   v
SPA
   |
   | /token + code_verifier
   v
Okta
   |
   | access/ID tokens
   v
SPA
   |
   | Authorization: Bearer <access_token>
   v
API
```

There is no useful long-term client secret to hide in JavaScript. PKCE is central.

### Token storage is an architectural choice

For browser apps, do not memorize “localStorage is always correct” or “cookies are always correct.” Understand the security tradeoff.

Browser JavaScript-accessible storage means XSS can become token theft. In-memory storage reduces persistence but does not magically stop XSS. A BFF can keep OAuth tokens on the server and expose only an HttpOnly application session cookie to the browser.

For this 15-day course, you need to recognize these choices and be able to discuss them. You do not need to become a browser-security specialist.

### Why Postman can mislead you

Postman proves an OAuth endpoint/API can work with the request you sent. It does not prove the browser architecture is correct.

A SPA can fail because of:

```text
CORS
Trusted Origin
cookie restriction
callback route
lost state/PKCE verifier
mixed content
browser storage
```

while the same token request works in Postman.

### Implement both

For the web app, identify:

```text
where state is stored
where verifier is stored
who calls /token
where client credential lives
where tokens live
what creates the local app session
```

For the SPA, identify the same items.

Then compare them explicitly.

### Break/fix

Web app:

- wrong client secret
- callback mismatch
- local application session not created after successful OIDC login

SPA:

- CORS/origin problem
- PKCE verifier lost after browser navigation
- callback route not handled

The goal is to stop saying “OAuth problem” when the real problem is application session code or browser state management.

---
