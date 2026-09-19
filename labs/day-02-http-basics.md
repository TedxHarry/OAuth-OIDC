# Day 2 Lab - Read Real HTTP Requests

## Purpose

This lab makes the Day 2 HTTP concepts visible.

You will run a small HTTP server on your own computer and inspect real requests with:

- Chrome or Edge DevTools
- Postman

No Okta application is required.

Complete the Day 2 lesson first:

[Day 2 - Understand the HTTP Transaction](../lessons/day-02-http-transaction.md)

## What you will observe

You will inspect:

- GET request
- path
- query parameters
- request headers
- 200 response
- 302 redirect
- `Location` header
- callback query parameters
- cookies
- POST body
- form encoding
- Authorization header
- 401 response
- successful bearer-token request

## Part 1 - Start the local server

From the repository root:

```bash
python scripts/python/day02_http_lab_server.py
```

You should see:

```text
Day 2 HTTP lab server running at http://localhost:8000
Press Ctrl+C to stop.
```

Leave that terminal open.

Then open:

```text
http://localhost:8000
```

in Chrome or Edge.

## Part 2 - Open browser DevTools

Open DevTools.

In Chrome or Edge:

```text
F12
```

or:

```text
Ctrl + Shift + I
```

Open the Network tab.

Enable:

```text
Preserve log
```

Clear the existing requests so the next test is easy to follow.

## Part 3 - GET and query parameters

Open:

```text
http://localhost:8000/hello?name=Harish&topic=OAuth
```

Find the `hello` request in the Network tab.

Record:

```text
Method:
Status:
Full URL:
Path:
Query parameter name:
Query parameter topic:
```

Open the response.

The server returns what it received.

Explain:

1. Which part of the URL is the path?
2. Which part is the query string?
3. How are the two query parameters separated?

## Part 4 - Observe a 302 redirect

Clear the Network tab.

Open:

```text
http://localhost:8000/redirect
```

Do not look only at the final page.

With Preserve log enabled, find both requests.

You should see something similar to:

```text
/redirect
-> 302

/callback?code=demo-code&state=demo-state
-> 200
```

Select the `/redirect` request.

Find the response header:

```http
Location: /callback?code=demo-code&state=demo-state
```

Now answer:

1. What status did `/redirect` return?
2. Which header told the browser where to go?
3. What request did the browser make next?
4. Which query parameters reached the callback?

This is the basic redirect behavior that browser-based OAuth/OIDC uses.

Do not assign OAuth meaning to `code` and `state` yet. Day 3 teaches those.

## Part 5 - Observe cookie behavior

Open:

```text
http://localhost:8000/set-cookie
```

Inspect the response headers.

Find:

```http
Set-Cookie: demo_session=abc123
```

Now open:

```text
http://localhost:8000/show-cookie
```

Inspect the request headers.

Find the `Cookie` header.

Answer:

1. Which response created the cookie?
2. Which later request returned it?
3. Did you manually type the Cookie header into the browser request?
4. What does this tell you about browser cookie behavior?

## Part 6 - Send a form-encoded POST from Postman

Create a Postman request:

```text
POST http://localhost:8000/form
```

Under Body, choose:

```text
x-www-form-urlencoded
```

Add:

| Key | Value |
|---|---|
| name | Harish |
| topic | OAuth |
| day | 2 |

Send the request.

Inspect both the request and response.

Record:

```text
Method:
Content-Type:
Request body:
Status:
Parsed form values returned by the server:
```

Find this header:

```http
Content-Type: application/x-www-form-urlencoded
```

This encoding will matter when you build real OAuth token requests later.

## Part 7 - Call a protected endpoint without a bearer token

In Postman:

```text
GET http://localhost:8000/protected
```

Do not configure Authorization yet.

Send the request.

Expected result:

```text
401
```

Inspect:

- status
- response body
- `WWW-Authenticate` response header

Answer:

> What credential was missing?

## Part 8 - Send the bearer token

In Postman, add this request header:

```http
Authorization: Bearer demo-token
```

Send the same request again.

Expected result:

```text
200
```

Compare the failed and successful requests.

The URL did not change.

The method did not change.

The important change was:

```http
Authorization: Bearer demo-token
```

## Part 9 - Break it deliberately

Change:

```http
Authorization: Bearer demo-token
```

to:

```http
Authorization: Bearer wrong-token
```

Send the request again.

Expected result:

```text
401
```

Now explain the failure using evidence.

Use this format:

```text
Last successful step:
Failed request:
Status:
Credential sent:
Expected credential:
Root cause:
```

Do not say only:

> Authentication failed.

Be specific about the HTTP evidence.

## Part 10 - Compare browser and Postman

Answer:

1. Which tool followed the redirect automatically in your test?
2. Which tool automatically returned the browser cookie?
3. Which tool gave you direct control over the Authorization header?
4. Why will this difference matter later when comparing "works in Postman" with "fails in browser"?

## Part 11 - Explain the transaction in plain language

Explain these three examples without reading the lesson.

### Redirect

```text
GET /redirect
-> 302
-> Location header
-> browser requests callback
```

### Cookie

```text
server sends Set-Cookie
-> browser stores cookie
-> browser returns Cookie header later
```

### Bearer token

```text
client sends Authorization header
-> API evaluates bearer token
-> accepted request returns 200
-> missing or bad token returns 401 in this lab
```

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### GET test

Path:

```text
/hello
```

Query string:

```text
name=Harish&topic=OAuth
```

The two query parameters are separated by `&`.

### Redirect test

`/redirect` returns a 302.

The `Location` response header tells the browser to request:

```text
/callback?code=demo-code&state=demo-state
```

The browser then makes the callback request.

### Cookie test

The server creates the cookie using `Set-Cookie`.

The browser later returns the cookie in the `Cookie` request header.

The browser handles this automatically according to cookie rules.

### Form POST

The request uses:

```text
POST
Content-Type: application/x-www-form-urlencoded
```

The form fields are carried in the request body.

### Protected endpoint

No bearer token:

```text
401
```

Correct bearer token:

```text
200
```

Wrong bearer token:

```text
401
```

The important evidence is the Authorization request header and the response status/body.

</details>

## Completion check

Day 2 lab is complete when you can inspect an unfamiliar HTTP request and identify:

- who sent it
- method
- URL
- path
- query parameters
- headers
- body
- cookies
- status
- response headers
- response body
- redirect destination

You should also understand the practical difference between a browser carrying a front-channel transaction and an application making a direct request.
