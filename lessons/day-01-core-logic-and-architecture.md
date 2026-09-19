# Day 1 - Core OAuth/OIDC Logic and Architecture

Today we are not configuring Okta yet.

The goal is to understand what problem each component is solving. Later, when you see settings such as `client_id`, `redirect_uri`, `scope`, `audience`, or `client authentication`, you should know why they exist.

## Start with a real requirement

An application owner says:

> We have an Employee Portal. Employees should sign in with Okta, and after login the portal needs to call an Employee API to retrieve their profile.

This sounds like one requirement, but it contains two separate problems.

```text
Problem 1
Who is this employee?
        |
        v
Authentication

Problem 2
Is this caller allowed to read Employee API data?
        |
        v
Authorization
```

Keep these separate.

## Authentication

A user opens:

```text
https://employee.company.com
```

The Employee Portal does not yet know who the user is.

It sends the user to Okta.

```text
Employee
   |
   v
Employee Portal
   |
   | Need this user authenticated
   v
Okta
```

The user authenticates with Okta.

That may include:

```text
username
password
MFA
```

After successful authentication, the application needs a standard way to learn that Okta authenticated the user.

This is where OpenID Connect, or OIDC, fits.

The client application receives an ID token that contains information about the authentication and the user.

```text
Employee
   |
   v
Okta
   |
   | authentication successful
   v
ID token
   |
   v
Employee Portal
```

The important relationship is:

```text
ID token
   |
   v
Client application
```

The Employee Portal consumes the ID token because it needs information about the signed-in user.

## API authorization

The Employee Portal also needs to call:

```http
GET /api/profile
```

on the Employee API.

The API has a different question.

It needs to know:

> Is this caller allowed to call this API operation?

This is where the OAuth access token fits.

```text
Employee Portal
       |
       | Authorization: Bearer <access_token>
       v
Employee API
```

The API receives the access token and evaluates it.

For example:

```text
Is the token valid?
Is it from the expected issuer?
Is it intended for this API?
Has it expired?
Does it contain the required permission?
```

If the token is valid and the required permission is present:

```text
GET /api/profile
        |
        v
200 OK
```

Now keep these two token relationships clear:

```text
ID token
   |
   v
Employee Portal

Access token
   |
   v
Employee API
```

Do not stop at memorizing:

```text
ID token = authentication
Access token = authorization
```

Ask a better question:

> Who is supposed to consume this token?

That question will help you troubleshoot many real integrations.

## Where OIDC and OAuth fit together

A normal user login flow can involve both OIDC and OAuth.

```text
User signs in
   |
   v
Okta authenticates the user
   |
   +--> ID token ------> Client application
   |
   +--> Access token --> API
```

OIDC gives the client information about the authenticated user.

OAuth provides access tokens for protected APIs.

People often say "OAuth login." As the implementation engineer, separate the actual requirements:

```text
User authentication
        |
        v
OIDC

API access
        |
        v
OAuth
```

## Map the actors to the project

For the Employee Portal example:

| OAuth/OIDC term | Project component |
|---|---|
| End user / resource owner | Employee |
| Client | Employee Portal |
| Authorization server | Okta |
| OpenID Provider | Okta when OIDC is used |
| Resource server | Employee API |
| Protected resource | Employee profile data or API operation |

Look at the relationships rather than memorizing the names.

The Employee Portal asks Okta for authentication and tokens.

```text
Employee Portal
      =
Client
```

The Employee API receives and validates access tokens.

```text
Employee API
     =
Resource Server
```

Okta issues the tokens.

```text
Okta
 =
Authorization Server
```

## Public and confidential clients

This is an important design decision.

### React SPA

Suppose the Employee Portal is a React SPA running in the browser.

If you place a client secret in JavaScript:

```javascript
const clientSecret = "SUPER-SECRET-123";
```

the user can inspect it.

The user controls the browser and can inspect:

```text
page source
JavaScript bundles
DevTools
network requests
browser storage
```

So a browser SPA cannot safely keep a client secret.

```text
React SPA
   |
   v
Public client
   |
   v
No client secret
   |
   v
Authorization Code + PKCE
```

We will study PKCE in detail on Day 3.

For now, understand the reason.

The browser cannot protect a long-lived client credential from the person using that browser.

### Server-side application

Now suppose the application is a server-side Java web application.

```text
Browser
   |
   v
Java Web Server
```

The Java server runs on infrastructure controlled by the organization.

It may be able to protect:

```text
client secret
private key
```

So it can operate as a confidential client.

```text
Java server-side application
        |
        v
Confidential client
        |
        v
Can authenticate itself to /token
```

A confidential client can also use PKCE.

Client authentication and PKCE solve different problems. We will cover that later.

### The question to ask

Do not classify a client as confidential just because Okta can generate a secret for it.

Ask:

> Can this component actually protect the credential from the end user?

## Add a scheduled Python job

The company also says:

> Every night at 1 AM, a Python job needs to call the Employee API.

Ask the first question:

> Is a human user present?

No.

There is nobody sitting at a browser at 1 AM.

A browser login does not fit this requirement.

Instead:

```text
Scheduled Python Job
        |
        | authenticates as itself
        v
      Okta
        |
        | access token
        v
Scheduled Python Job
        |
        | Authorization: Bearer <access_token>
        v
   Employee API
```

This is a service-to-service pattern.

Later we will use Client Credentials for this type of integration.

Because there is no user:

```text
No browser login
No user authentication
No ID token
Access token required
```

The service needs permission to call an API. It does not need proof that a human user signed in.

## Frontend, backend, API, and Okta are different components

A real system may contain:

```text
Browser
Frontend application
Backend application
API
Background service
Okta
```

Do not treat them as one thing.

This matters when troubleshooting.

If `/authorize` fails, ask:

> Which component started that request?

If `/token` fails, ask:

> Which component called the token endpoint?

If:

```http
GET /api/profile
```

returns `401`, ask:

> Which component rejected the request?

It may be the API, even though the user successfully authenticated with Okta.

A real ticket may say:

> Okta login is broken.

But the actual transaction may show:

```text
Okta authentication succeeded
        |
        v
authorization code returned
        |
        v
tokens issued
        |
        v
API rejected access token
```

In that case, authentication is not the failed layer.

Throughout this course, keep asking:

> Which component made this request, and which component rejected it?

## OAuth/OIDC does not do provisioning

The application owner adds another requirement:

> When someone joins the company, create their SaaS account. When they leave, disable it.

That is a separate problem.

```text
OIDC
-> authentication and SSO

OAuth
-> API authorization

SCIM or application API
-> account provisioning and lifecycle

SAML
-> another enterprise SSO protocol
```

This course stays focused on OAuth and OIDC, but you need to recognize where they stop.

A successful OIDC login does not automatically create, update, disable, or delete an account in the target application.

# Day 1 Lab

Use this scenario:

```text
React Employee Portal
Java Employee API
Okta
Scheduled Python Job
```

The Python job also needs to call the Employee API every night.

## Part 1 - Classify the components

Complete this table without looking back at the lesson if possible.

| Component | Human user in its flow? | Public / Confidential / Neither | Main responsibility |
|---|---|---|---|
| React Employee Portal | ? | ? | ? |
| Java Employee API | ? | ? | ? |
| Scheduled Python Job | ? | ? | ? |
| Okta | ? | ? | ? |

## Part 2 - Answer these questions

1. What proves to the React application that the employee authenticated?
2. What should the React application send to the Java API?
3. Why should we not put a client secret inside the React application?
4. Why does the scheduled Python job not need an ID token?

## Part 3 - Draw the employee path

Start with:

```text
Employee
   |
   v
React Employee Portal
   |
   v
Okta
   |
   v
React Employee Portal
   |
   v
Employee API
```

Label:

- where authentication happens
- where the ID token goes
- where the access token goes
- which component consumes each token

## Part 4 - Draw the scheduled-job path

Start with:

```text
Scheduled Python Job
        |
        v
      Okta
        |
        v
Scheduled Python Job
        |
        v
   Employee API
```

Explain:

- why there is no browser
- why there is no user login
- why there is no ID token
- what the access token is used for

## Part 5 - Find the problem in each statement

Explain what is wrong with each statement.

### Statement 1

> We will put the Okta client secret in the React source code.

### Statement 2

> The Employee API can accept the ID token because it proves the user logged in.

### Statement 3

> The scheduled Python job can use the same browser login flow as an employee.

### Statement 4

> OIDC will create the user's SaaS account and disable it when the employee leaves.

## Part 6 - Explain the design to an application owner

Give a short explanation in your own words.

Cover these points:

```text
OIDC handles ...
OAuth handles ...
React is ...
The scheduled job is ...
The API consumes ...
```

Keep the explanation short enough that you could say it during a project meeting.

# Day 1 Completion Check

Before moving to Day 2, you should be able to look at an application diagram and identify:

- the end user
- the client
- the authorization server
- the resource server/API
- whether authentication is required
- whether API authorization is required
- whether the client is public or confidential
- whether a human user is present
- which component consumes the ID token
- which component consumes the access token

Do not move to Day 2 just because the definitions look familiar.

Move on when you can explain the relationships without reading them from the page.
