# Day 2 - Understand the HTTP Transaction

## Goal for today

OAuth and OIDC happen over HTTP.

Before learning Authorization Code + PKCE, you need to be comfortable reading what the browser, application, authorization server, and API actually send to each other.

By the end of Day 2, you should understand:

- HTTP request and response
- method
- URL
- path
- query parameters
- headers
- request body
- response body
- status codes
- redirects
- cookies
- the `Authorization` header
- bearer tokens
- browser requests vs direct application requests
- front-channel vs back-channel communication
- how to inspect traffic with browser DevTools and Postman

You do not need an Okta application for today's lab.

[Open the Day 2 flow diagrams](../diagrams/day-02-http-flow.md)

## Why HTTP matters

Many OAuth problems are reported like this:

> Login is not working.

That description does not tell you where the failure occurred.

A real sign-in is a sequence of HTTP requests and responses.

Later, an OAuth/OIDC transaction will look roughly like this:

```text
Browser requests application
        |
        v
Application starts authorization
        |
        v
Browser goes to Okta
        |
        v
Okta redirects browser back
        |
        v
Application exchanges information with Okta
        |
        v
Application calls API
```

If something fails, you need to locate the failed transaction.

A useful troubleshooting question is:

> What is the last HTTP step I can prove succeeded?

Day 2 teaches you how to read those steps.

## HTTP request and response

HTTP communication is based on requests and responses.

A client sends a request.

A server sends a response.

```text
Client
   |
   | HTTP request
   v
Server
   |
   | HTTP response
   v
Client
```

The client might be:

```text
browser
Postman
Python application
Java application
mobile application
backend service
```

The server might be:

```text
Okta
web application
API
authorization server
resource server
```

## Anatomy of an HTTP request

Consider:

```http
GET /employees?department=HR HTTP/1.1
Host: api.example.com
Accept: application/json
Authorization: Bearer eyJ...
```

There are several pieces.

### Method

```text
GET
```

The method tells the server what kind of operation is being requested.

Common methods you will see in this course:

| Method | Typical purpose |
|---|---|
| GET | Retrieve a page, resource, or start a browser request |
| POST | Send data to a server |
| PUT | Replace or update a resource |
| PATCH | Partially update a resource |
| DELETE | Delete a resource |

For OAuth/OIDC, you will frequently see GET and POST.

### URL

The full URL might be:

```text
https://api.example.com/employees?department=HR
```

Break it into pieces:

```text
https
  |
  | scheme
  v
https://api.example.com/employees?department=HR
        |               |          |
        |               |          |
        v               v          v
       host            path      query string
```

### Path

```text
/employees
```

The path identifies the resource or endpoint on the server.

Later you will see Okta endpoints such as:

```text
/authorize
/token
/userinfo
/introspect
/revoke
```

Do not memorize those today.

Just understand what an endpoint path is.

### Query parameters

This URL:

```text
https://api.example.com/employees?department=HR&status=active
```

contains two query parameters:

```text
department = HR
status     = active
```

They appear after the `?`.

Multiple parameters are normally separated by `&`.

OAuth authorization requests contain many query parameters.

Later you will see things such as:

```text
client_id
redirect_uri
response_type
scope
state
nonce
code_challenge
```

Day 3 explains what those mean.

Today, learn how to find them.

## URL encoding

Some characters cannot be placed into a URL in their normal form.

For example:

```text
https://app.example.com/callback
```

may appear inside another URL as:

```text
https%3A%2F%2Fapp.example.com%2Fcallback
```

That is URL encoding.

It does not mean the value is encrypted.

It is still the same value represented safely inside a URL.

This distinction matters during troubleshooting.

## Headers

HTTP headers provide additional information about the request or response.

Example:

```http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer eyJ...
Cookie: demo_session=abc123
```

Headers matter heavily in OAuth.

You will frequently inspect:

```text
Authorization
Content-Type
Accept
Location
Cookie
Set-Cookie
Origin
WWW-Authenticate
```

## Request body

A POST request can send data in its body.

Example:

```http
POST /example HTTP/1.1
Content-Type: application/x-www-form-urlencoded

name=Harish&department=IAM
```

The body contains:

```text
name       = Harish
department = IAM
```

OAuth token requests commonly use:

```text
Content-Type: application/x-www-form-urlencoded
```

That means parameters are sent in form-encoded format.

For example:

```text
grant_type=...
&code=...
&redirect_uri=...
```

You will build a real token request later.

## Anatomy of an HTTP response

A server response contains a status code, headers, and often a body.

Example:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "name": "Harish",
  "department": "IAM"
}
```

### Status code

```text
200
```

The status code is your first clue about what happened.

### Response headers

Example:

```http
Content-Type: application/json
```

or:

```http
Location: https://app.example.com/callback
```

### Response body

The response body may contain:

```text
HTML
JSON
plain text
error details
token response
API data
```

## Status codes you need first

You do not need every HTTP status code.

Start with these:

### 200

```text
200 OK
```

The request completed successfully.

### 302

```text
302 Found
```

This commonly means:

> Go to another URL.

The new URL is normally provided in the `Location` response header.

A 302 is often completely normal in browser authentication.

### 400

```text
400 Bad Request
```

The server rejected the request because something about the request is invalid.

Later, OAuth errors such as invalid parameters can appear with 400 responses.

### 401

```text
401 Unauthorized
```

Despite the name, a 401 normally means the request does not have acceptable authentication credentials for the protected resource.

For an API protected by OAuth, think first about the access token.

Examples:

```text
no token
malformed token
expired token
untrusted token
wrong token
```

The exact cause still needs evidence.

### 403

```text
403 Forbidden
```

The server understood the request but will not allow the operation.

In a protected API, a common pattern is:

```text
token accepted
but
required permission is missing
```

Do not turn 401 vs 403 into an absolute rule for every application.

Different products and frameworks can return errors differently.

Use the status code as a clue, then inspect the response and server behavior.

## Redirects

Redirects are extremely important in browser-based OAuth/OIDC.

Imagine the browser requests:

```http
GET /start
```

The server responds:

```http
HTTP/1.1 302 Found
Location: /callback?code=demo-code&state=demo-state
```

The browser reads the `Location` header and requests the new URL.

```text
Browser
   |
   | GET /start
   v
Server
   |
   | 302
   | Location: /callback?code=demo-code&state=demo-state
   v
Browser
   |
   | GET /callback?code=demo-code&state=demo-state
   v
Server
```

The browser did not receive a normal page and decide on its own to visit the callback.

The HTTP response instructed it to go there.

## Why redirects matter in OAuth

Later, the browser will go from your application to Okta and then back to your application's callback.

A simplified shape is:

```text
Browser
   |
   | authorization request
   v
Okta
   |
   | HTTP redirect
   | Location: application callback
   v
Browser
   |
   | callback request
   v
Application
```

The exact Authorization Code flow comes on Day 3.

For now, learn how to recognize the redirect itself.

## Front channel

The front channel means the browser participates in carrying the transaction.

Example:

```text
Application
   |
   | redirect browser
   v
Browser
   |
   | request to Okta
   v
Okta
```

and later:

```text
Okta
   |
   | redirect
   v
Browser
   |
   | callback request
   v
Application
```

The browser can see and carry values used in this part of the flow.

That does not mean every value in OAuth should travel through the browser.

## Back channel

The back channel is direct communication between application components without the user's browser carrying the request.

Example:

```text
Backend application
       |
       | HTTPS request
       v
      Okta
```

or:

```text
Backend service
       |
       | HTTPS API request
       v
      API
```

For a server-side web application, the token exchange can happen from the backend directly to the token endpoint.

The browser does not need to see the client secret used by the backend.

Later you will compare this with a SPA using PKCE.

## Cookies

A cookie is data a server asks the browser to store and return on later requests to the appropriate site.

A server might respond:

```http
Set-Cookie: demo_session=abc123; HttpOnly; SameSite=Lax
```

On a later request, the browser may send:

```http
Cookie: demo_session=abc123
```

Cookies are important because browser sessions commonly depend on them.

Later you will separate:

```text
Okta browser session
application session
ID token
access token
refresh token
```

They are not the same thing.

For Day 2, understand only this:

> A browser can automatically send cookies for the appropriate site.

That automatic behavior is different from an application intentionally adding a bearer token to an API request.

## Bearer access token in an HTTP request

A protected API request commonly looks like:

```http
GET /api/profile HTTP/1.1
Host: api.example.com
Authorization: Bearer <access_token>
```

The important part is:

```http
Authorization: Bearer <access_token>
```

Bearer means possession of the token is sufficient to present it as the credential.

That is one reason access tokens must be protected from unnecessary exposure.

Do not put access tokens into URLs.

URLs can be copied, cached, stored in browser history, or logged.

Use the HTTP Authorization header for bearer access tokens.

## Browser vs Postman

A browser and Postman can send HTTP requests, but they do not behave exactly the same way.

A browser automatically participates in things such as:

```text
redirect navigation
browser cookies
same-origin rules
CORS enforcement
interactive sign-in pages
```

Postman is an API client.

It is useful for inspecting and controlling:

```text
method
URL
headers
body
authentication header
response
```

This difference becomes useful later.

For example:

```text
Postman works
browser fails
```

may point toward browser-specific behavior.

But do not jump to CORS before proving where the failure occurs.

## Browser DevTools Network tab

For OAuth troubleshooting, the Network tab is one of your most useful tools.

In Chrome or Edge:

```text
F12
or
Ctrl + Shift + I
```

Then open:

```text
Network
```

Useful columns include:

```text
Name
Status
Type
Initiator
Time
```

When you select a request, inspect:

```text
Headers
Payload
Response
Cookies
Timing
```

For redirects, enable:

```text
Preserve log
```

Otherwise navigation can make earlier requests harder to follow.

## What to record when troubleshooting

For an important request, write down:

```text
Who made the request?
What method was used?
What URL was called?
What query parameters were sent?
What important headers were sent?
Was there a request body?
What status came back?
What important response headers came back?
What did the response body say?
Was there a redirect?
Where did it redirect?
```

This is much stronger than saying:

> Login failed.

## A first troubleshooting example

Suppose you see:

```text
GET /start
-> 302

GET /callback?code=demo-code&state=demo-state
-> 200
```

You can already prove:

```text
/start responded
redirect happened
browser reached /callback
query parameters reached callback
```

If the application fails after that, you should investigate the next transaction rather than the initial redirect.

That is the habit we are building.

## Common mistakes to catch early

### Mistake 1: Treating a redirect as an error

A 302 is often normal in a browser authentication flow.

### Mistake 2: Looking only at the final page

The final page can hide several requests and redirects that happened first.

Use the Network tab.

### Mistake 3: Assuming URL encoding is encryption

`%2F` and similar sequences are encoding, not secrecy.

### Mistake 4: Putting a bearer token into the URL

Use the Authorization header instead.

### Mistake 5: Blaming CORS for every browser problem

First prove which request failed and which component rejected it.

### Mistake 6: Calling every 401 an Okta login failure

A 401 from your API can occur after Okta authentication succeeded.

## What you should be able to explain now

Without looking back, explain:

1. What is an HTTP request?
2. What is an HTTP response?
3. What is the difference between a URL path and query parameters?
4. What is a header?
5. What is a request body?
6. What does a 302 tell the browser?
7. Why are redirects important in OAuth/OIDC?
8. What is the front channel?
9. What is the back channel?
10. What is a cookie?
11. How is a cookie different from a bearer token?
12. Where is a bearer token normally sent?
13. Why is browser DevTools useful?
14. What is the first question to ask when tracing a failed transaction?

## Day 2 lab

Now perform the local HTTP lab:

[Day 2 Lab - Read Real HTTP Requests](../labs/day-02-http-basics.md)

The lab uses a small Python server running on your own computer.

You will inspect:

- GET request
- query parameters
- 302 redirect
- `Location` header
- callback query parameters
- cookie behavior
- POST form body
- Authorization header
- 401 response
- successful bearer-token request

No Okta application is required.

## Day 2 completion standard

Day 2 is complete when you can open a browser or Postman request and identify:

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
- redirect location

You should also be able to explain whether the browser or another application component carried the transaction.

## Official references

These are reference material. You do not need to read them before completing the lesson.

- [Okta: OAuth 2.0 and OpenID Connect overview](https://developer.okta.com/docs/concepts/oauth-openid/)
- [Okta: Token lifecycle](https://developer.okta.com/docs/concepts/token-lifecycles/)
- [Okta: API Access Management](https://developer.okta.com/docs/concepts/api-access-management/)
