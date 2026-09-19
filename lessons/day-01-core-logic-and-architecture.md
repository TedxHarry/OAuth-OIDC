## Day 1 — Understand the core logic before touching configuration

### Start with a real requirement

Assume an application owner says:

> We have an Employee Portal. Employees should sign in with Okta, and the portal needs to call an Employee API to read their profile.

Do not start by creating an Okta application. First split that sentence into two separate problems.

```text
Problem 1: Who is the employee?
           → authentication

Problem 2: May this caller read Employee API data?
           → authorization
```

That distinction is the foundation for everything that follows.

### Where OIDC and OAuth fit

For the first problem, the application needs a standard way to learn that Okta authenticated a user. That is the OIDC side.

For the second problem, the API needs a credential representing permitted access. That is the OAuth access-token side.

Think of the result this way:

```text
User signs in
   |
   v
Okta authenticates the user
   |
   +--> ID token ----> Client application
   |                   "Here is information about the authenticated user"
   |
   +--> Access token -> Resource API
                       "This caller has these API permissions"
```

Do not reduce this to “ID token means authentication, access token means authorization” and stop there. Ask **who consumes each artifact**. The ID token is issued for the client application. The access token is issued for the resource server/API.

### Learn the actors by mapping them to a project

For the Employee Portal:

```text
Resource owner / end user = Employee
Client                     = Employee Portal
Authorization server       = Okta
OpenID Provider            = Okta when OIDC is used
Resource server            = Employee API
Protected resource         = Employee profile data/API operation
```

If you can map those actors from a project diagram, OAuth terminology becomes much easier.

### Public vs confidential client — understand the reason

Suppose the Employee Portal is a React SPA running in the browser.

Any secret shipped with the JavaScript can be inspected by the user. Therefore:

```text
React SPA
→ public client
→ cannot rely on a client secret
→ Authorization Code + PKCE
```

Now suppose the application is a server-side Java web application. The client credential can stay on infrastructure controlled by the company:

```text
Java server-side web app
→ confidential client
→ can authenticate itself to /token
→ can also use PKCE
```

The key question is not “does Okta show a client-secret field?” The key question is:

> Can this component actually keep that credential confidential from the end user?

### Frontend vs backend — identify the component making the request

A real application may contain several OAuth-relevant components:

```text
Browser / frontend
Backend web application
API
Background service
```

They are not interchangeable.

If the browser redirects to `/authorize`, that does not mean the backend made the request. If the backend exchanges a code at `/token`, that does not mean the browser possesses the client secret. If the API receives an access token, the API does not need the user's browser cookie to validate that token.

When troubleshooting later, always ask:

> Which component made this request?

That question eliminates a lot of confusion.

### Know where OAuth/OIDC stops

Suppose the application owner also says:

> When the user joins the company, create their account in the SaaS application, and when they leave, disable it.

That is not solved just because OIDC login works.

```text
OIDC       → authentication / SSO
OAuth      → API authorization
SCIM/API   → provisioning and lifecycle
SAML       → another enterprise SSO protocol
```

You only need the boundary here. SAML and SCIM deserve their own courses.

### Your lab today

Take these five requirements and classify them before configuring anything:

1. React portal with employee login and backend API.
2. Java web app with employee login only.
3. Nightly Python job calling an internal API.
4. PowerShell automation calling Okta Management APIs.
5. SaaS app that needs SSO plus user provisioning.

For each, write:

```text
Is there a user?
Client type?
Authentication needed?
API authorization needed?
Provisioning needed?
Likely OAuth/OIDC flow?
```

### Explain-back checkpoint

You should be able to explain this naturally:

> OIDC tells the application about the authenticated user. OAuth gives clients access tokens for APIs. They often appear in the same login flow, but they solve different problems. Before I choose a flow, I first identify the client type, whether there is a user, and which component needs access to which resource.

If that explanation makes sense to you rather than feeling memorized, Day 1 is complete.

---
