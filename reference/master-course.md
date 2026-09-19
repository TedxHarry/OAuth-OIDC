# OAuth & OIDC for Okta Implementation Engineers

**15-day practical track — implementation, integration, automation, and troubleshooting**

**Master version:** reference curriculum + detailed mentor-led lessons + labs + troubleshooting drills + advanced second-pass appendix.

This course is built for one outcome: you should be able to walk into a real Okta/OAuth project, understand the requirement, choose the right design, configure it, integrate it, test it, troubleshoot it, and explain what is happening without guessing.

This is not a protocol-history course. You do not need to memorize RFCs, cryptographic mathematics, or every OAuth extension. You need the parts that repeatedly show up in engineering work, and you need to understand those parts deeply enough to reason through a problem when the documentation or error message is not obvious.

## What “job-ready” means here

By the end, you should be comfortable when an application owner says something vague like:

> We have a React frontend, a Java API, Okta, and a scheduled backend job. We need SSO and API security.

You should be able to turn that into concrete engineering decisions:

- What type of client is each component?
- Is the requirement authentication, API authorization, or both?
- Is there a user in the flow?
- Which OAuth/OIDC flow fits?
- Which Okta authorization server should issue the token?
- What redirect URIs, scopes, claims, audience, and grant types are needed?
- How does the client authenticate to the token endpoint?
- Where do PKCE, `state`, and `nonce` fit?
- Which token goes to the application and which goes to the API?
- How does the API validate the token?
- How is authorization enforced after validation?
- How are refresh, logout, revocation, and sessions handled?
- Which Okta policy layer controls token issuance, and which controls authentication/MFA?
- How will secrets or private keys be stored and rotated?
- What changes between dev, test, and production?
- When something fails, which request failed and how do you prove the cause?

The realistic goal is not “I know every OAuth feature ever created.” The goal is: **you can independently handle the common 80–90% of real implementation and support work, and you know how to investigate the remaining edge cases.**

---

# How to use this course

Do not stop at reading a topic. Run every important topic through this loop:

1. **Understand** it in plain English.
2. **Draw** who talks to whom.
3. **Run** it in Okta.
4. **Inspect** the actual HTTP requests, responses, cookies, and tokens.
5. **Break** one thing deliberately.
6. **Troubleshoot** where the transaction stopped and why.
7. **Explain** the failure and prove the diagnosis.

A topic is not complete because you recognize the terminology. You are done when you can explain, visualize, implement, and troubleshoot it.

## The three-source proof rule

For troubleshooting labs, do not accept “I changed this setting and it started working.” Prove the issue from evidence whenever the sources are available:

1. **Browser Network tab, curl, or Postman** — what exact request or response failed?
2. **Token inspection** — what was actually issued: issuer, audience, scopes, claims, expiry, `kid`?
3. **Okta System Log** — what did Okta evaluate, allow, or deny?

Then change the configuration, repeat the flow, and prove that the behavior changed for the reason you expected.

That habit matters more than memorizing a long list of OAuth errors.

## Build one continuous lab

Use the same small environment throughout the course:

```text
User
  |
Browser / React client
  |
Okta
  |
Java or Node API
  |
Protected resource
```

Later add:

```text
Scheduled service / Python or PowerShell
  |
OAuth service client
  |
Okta
  |
API or Okta Management API
```

You will keep extending and breaking the same system. This helps the concepts connect instead of becoming isolated definitions.

---

# Part 1 — The core understanding you actually need

## 1. Authentication, authorization, OIDC, and OAuth

Keep these distinctions clean:

- **Authentication:** who is this user?
- **Authorization:** what is this caller allowed to do?
- **OAuth 2.0:** obtains access tokens that clients use to access protected resources/APIs. Many flows represent delegated user access; Client Credentials represents the client itself with no user.
- **OpenID Connect (OIDC):** adds an identity/authentication layer on OAuth and introduces the ID token.

In normal project language, people often say “OAuth login.” As an engineer, translate that into the real requirement: **OIDC is being used to authenticate the user, while OAuth access tokens may separately authorize API access.**

## 2. The actors

Know these without thinking:

| OAuth/OIDC concept | In a normal Okta project |
|---|---|
| Resource owner / end user | The user |
| Client / relying party | The application asking for tokens |
| Authorization server / OpenID Provider | Okta |
| Resource server | Your protected API |
| Protected resource | Data or operation behind the API |

Basic shape:

```text
User
  |
  v
Client application
  |
  | authorization / authentication
  v
Okta Authorization Server
  |
  | tokens
  v
Client
  |
  | Authorization: Bearer <access_token>
  v
Resource Server / API
```

## 3. Public vs confidential clients

This decision affects almost everything that follows.

### Public client

Examples: browser SPA, mobile/native app.

The user controls the device or can inspect the application code. A long-lived client secret cannot be kept secret.

Typical model:

```text
Authorization Code + PKCE
client authentication = none
```

### Confidential client

Examples: server-side web application, backend service.

It can keep credentials on infrastructure controlled by the organization.

Possible client authentication:

```text
client_secret_basic
client_secret_post
private_key_jwt
```

A confidential client can also use **PKCE**. Do not learn “client secret OR PKCE” as if they solve the same problem.

- Client authentication proves the client's identity to the authorization server.
- PKCE protects the authorization-code exchange from code interception/injection.

## 4. Frontend vs backend responsibility

When troubleshooting, always ask which component made the request.

A browser may handle redirects and user interaction. A backend may perform the token exchange and hold tokens. A SPA may perform the token exchange itself with PKCE. A backend-for-frontend design may keep OAuth tokens away from browser JavaScript and give the browser only an application session cookie.

You do not need to master every architecture now. You do need to know **where the token lives and which component called Okta or the API**.

## 5. Know the boundaries: OIDC/OAuth vs SAML vs SCIM

An implementation engineer should also know when OAuth/OIDC is not the whole solution.

- **OIDC:** modern application authentication/SSO.
- **OAuth:** API authorization.
- **SAML:** common browser SSO protocol, especially for enterprise SaaS.
- **SCIM or application APIs:** account provisioning and lifecycle management.

OIDC login does **not** by itself create, update, disable, or delete the user's downstream account. That is a provisioning problem, usually SCIM or an application-specific API.

Do not turn this course into a SAML or SCIM course. Just keep the boundary clear when gathering requirements.

---

# Part 2 — Read the network before touching configuration

Most OAuth issues become easier when you can answer: **which machine called which endpoint, with what data, and what came back?**

## Front channel

Traffic through the browser, typically redirects:

```text
Browser
  |
  | GET /authorize
  v
Okta
  |
  | 302 redirect
  v
Browser -> redirect_uri?code=...&state=...
```

## Back channel

A direct client-to-server call:

```text
Application / SPA
  |
  | POST /token
  v
Okta
  |
  | tokens
  v
Application
```

## API call

```http
GET /api/employees
Authorization: Bearer eyJ...
```

## HTTP knowledge you need

You do not need a separate HTTP course, but you must comfortably read:

- GET vs POST
- query parameters
- form-encoded POST bodies
- request and response headers
- `Authorization: Bearer`
- cookies
- redirects and `Location`
- browser origin
- CORS failures
- basic TLS/HTTPS behavior
- HTTP 302, 400, 401, and 403

Typical interpretation:

| Result | First interpretation |
|---|---|
| 302 | Usually a normal redirect during browser authorization |
| 400 from OAuth endpoint | Request, client authentication, grant, redirect URI, scope, or code problem |
| 401 from API | Token missing or unacceptable: invalid, expired, wrong issuer/audience/signature, etc. |
| 403 from API | Caller is authenticated/token is accepted, but authorization is insufficient |

Do not treat those as absolute rules for every framework. Use them as the first place to look.

---

# Part 3 — Choose the flow from the requirement

You should be able to make these decisions quickly.

## User + SPA or native/mobile app

```text
Authorization Code + PKCE
public client
no client secret in browser/mobile code
```

## User + server-side web app

```text
Authorization Code + PKCE
confidential client
client authentication at /token
```

The server can keep a client secret or private key. PKCE is still useful and Okta recommends Authorization Code + PKCE where possible.

## No user + service-to-service API

```text
Client Credentials
confidential client
access token
no ID token
```

## No user + Okta Management APIs

```text
OAuth API Service app
Client Credentials
private_key_jwt
Org Authorization Server
Okta API scopes
admin role/resource assignment
```

For Okta API service apps, scopes alone are not the whole authorization model. The service app also needs appropriate admin roles/resource access for least privilege.

## Embedded Identity Engine authentication

Recognize only:

```text
Interaction Code
```

Okta Identity Engine uses Interaction Code for embedded authentication experiences. Know that it exists and why it appears. Do not spend the 15-day course mastering it unless your project specifically uses embedded authentication.

Redirect authentication is the main learning path for this course.

---

# Part 4 — Authorization Code + PKCE: know this flow cold

This is the flow to spend the most time on.

```text
1. Client creates a high-entropy code_verifier

2. Client derives:
   code_challenge = S256(code_verifier)

3. Browser -> Okta /authorize
   client_id
   redirect_uri
   response_type=code
   scope=openid ...
   state
   nonce
   code_challenge
   code_challenge_method=S256

4. User authenticates with Okta

5. Okta evaluates authentication policies and the authorization request

6. Okta -> redirect_uri
   ?code=...
   &state=...

7. Client validates state

8. Client -> /token
   grant_type=authorization_code
   code
   redirect_uri
   code_verifier
   + client authentication if the client is confidential

9. Okta verifies the code, client, redirect URI, PKCE verifier, and other request requirements

10. Okta returns applicable tokens
```

## Parameters you should be able to explain

| Parameter | Practical purpose |
|---|---|
| `client_id` | Identifies the application |
| `redirect_uri` | Approved callback location for the authorization response |
| `response_type=code` | Requests an authorization code |
| `scope` | Requests OIDC identity scopes and/or API permissions |
| `openid` | Makes the request an OIDC request |
| `state` | Correlates request/response and protects the browser authorization transaction against CSRF |
| `nonce` | Binds the ID token to the OIDC request and helps prevent replay |
| `code` | Short-lived, one-time authorization credential |
| `code_verifier` | High-entropy per-transaction PKCE value kept by the client |
| `code_challenge` | Derived form of the verifier sent with the authorization request |
| `code_challenge_method=S256` | Tells the server the secure SHA-256 PKCE method is used |
| `offline_access` | Requests refresh-token capability for Authorization Code flow |

### `offline_access` matters

If you expect a refresh token, do not only enable the Refresh Token grant in the Okta app. For Authorization Code flow, request `offline_access` on the **authorization request**.

Example scope request:

```text
openid profile email offline_access employee.read
```

Then the token exchange can return a refresh token if the application and authorization-server policy permit it.

## Failure labs

Break and diagnose:

- wrong `redirect_uri`
- wrong client ID
- missing or wrong `state`
- wrong `nonce`
- code reused
- code expired
- wrong PKCE verifier
- wrong token endpoint/issuer
- wrong client authentication
- refresh expected but `offline_access` was not requested

---

# Part 5 — Tokens and token lifecycle

Do not mix the three token types.

| Token | Consumed by | Job |
|---|---|---|
| ID token | Client application | Carries authentication information about the signed-in user |
| Access token | Resource server/API | Authorizes access to protected resources |
| Refresh token | Authorization server | Obtains replacement access/ID tokens without another interactive sign-in |

## Rule to keep forever

**Your API authorizes API calls with an access token, not an ID token.**

An ID token is about the authentication event for the client. It is not an API credential.

## Refresh lifecycle

Understand:

```text
Access token expires
      |
      v
Client presents refresh token to /token
      |
      v
New access token
(and possibly a new refresh token)
```

Know enough to work with:

- access-token lifetime
- refresh-token lifetime
- refresh-token rotation
- refresh-token reuse detection
- token revocation
- reauthentication after refresh is no longer possible

For SPAs, refresh-token rotation is especially relevant. Do not memorize every default lifetime; learn where the authorization-server access policy controls lifetimes and how to inspect what your environment actually uses.

---

# Part 6 — JWT, discovery, JWKS, validation, then authorization

You need JWTs deeply enough to troubleshoot them. You do not need RSA mathematics.

A JWT has three base64url-encoded parts:

```text
header.payload.signature
```

Common fields:

### Header

```json
{
  "alg": "RS256",
  "kid": "abc123"
}
```

### Payload

```json
{
  "iss": "https://example.okta.com/oauth2/default",
  "sub": "00u...",
  "aud": "api://employee-service",
  "exp": 1780000000,
  "iat": 1779996400,
  "scp": ["employee.read"]
}
```

## Discovery and keys

Do not hardcode signing keys.

```text
Issuer
  |
  v
/.well-known/openid-configuration
  |
  v
jwks_uri
  |
  v
JWKS
  |
  v
public key matching JWT kid
```

Libraries should cache and refresh signing keys. An `unknown kid` failure can occur around key rotation if a consumer incorrectly hardcodes keys or fails to refresh JWKS.

## Step 1: validate the token

The resource server checks things such as:

```text
Signature valid?
Expected signing algorithm?
Issuer correct?
Audience correct?
Token expired?
nbf valid if present?
Clock reasonable?
```

If validation fails, the token is not trusted.

## Step 2: authorize the request

Only after validation:

```text
Does the token contain the required scope/claim/role?
Does this caller have permission for this operation?
```

This separation is important:

```text
Token validation -> Can I trust this token?
Authorization    -> Is this trusted caller allowed to do this?
```

It also helps keep 401 and 403 reasoning clean.

## Local validation vs introspection

For tokens meant for your API from a Custom Authorization Server, local JWT validation is common and avoids a network call for every request.

The `/introspect` endpoint performs remote validation with Okta and reports whether a token is active. It adds a network dependency but can be useful when you need current revocation state rather than relying only on JWT signature/lifetime checks.

## Important Org Authorization Server rule

Access tokens issued by the **Org Authorization Server are for Okta to consume**. Your application should **treat them as opaque** and should not locally decode/validate or build logic around their contents. Their contents can change.

If you are protecting **your own API**, use a **Custom Authorization Server**.

---

# Part 7 — Okta application configuration

Create real app integrations and understand why each setting exists.

## Fields that matter day to day

| Setting | What it controls |
|---|---|
| Application type | Web, SPA, Native, API Service; affects client type and allowed behavior |
| Client ID | Application identifier |
| Client authentication | How a confidential client proves its identity to `/token` |
| Grant types | Which OAuth flows the app may use |
| Sign-in redirect URIs | Allowed callback destinations |
| Sign-out redirect URIs | Allowed post-logout destinations |
| Assignments / Controlled Access | Which users/groups can access the app |
| Trusted Origins | Browser origins permitted for relevant cross-origin Okta calls |

## App assignment nuance

If access is limited to assigned users/groups, an unassigned user cannot use the application. If the app's Controlled Access setting permits everyone in the organization, lack of an individual assignment is not the same failure.

Do not blindly assume “assignment issue.” Check the app's access model and System Log.

## Redirect URI discipline

Treat redirect URIs as exact security configuration. Typical mistakes:

- HTTP vs HTTPS
- wrong port
- wrong path
- wrong environment
- trailing path differences
- localhost URI not registered
- production callback accidentally pointing to test

## Custom domain discipline

Be consistent about issuer/domain configuration. If one component is configured for an Okta org domain and another expects a custom domain, issuer/discovery/JWKS/cookie behavior can become confusing.

Use discovery from the exact issuer the application is configured to trust.

---

# Part 8 — Client authentication: short section, high practical value

You should recognize these methods immediately.

## `none`

Used by public clients that cannot keep a credential, such as SPA/native clients using Authorization Code + PKCE.

## `client_secret_basic`

Client ID and client secret are sent in the HTTP Basic Authorization header to the token endpoint.

```http
Authorization: Basic base64(client_id:client_secret)
```

## `client_secret_post`

Client ID and client secret are sent in the token request body.

## `private_key_jwt`

The client signs a short-lived JWT assertion with its private key; Okta verifies it using the registered public key.

Know the important assertion fields conceptually:

```text
iss = client_id
sub = client_id
aud = full URL of the endpoint the assertion authenticates to
      (for /token client auth, the exact token endpoint URL,
       e.g. https://{yourOktaDomain}/oauth2/v1/token)
exp = short lifetime
kid = identifies registered public key when applicable
```

You do not need to hand-code JWT signing algorithms from scratch. You do need to understand what is being signed and how to diagnose a failure.

## `invalid_client` lab

Intentionally test:

- wrong secret
- wrong auth method
- secret in body when Basic is configured, or vice versa
- wrong private key
- unregistered/mismatched `kid`
- incorrect assertion audience
- expired client assertion

Also practice a basic secret/key rotation so you understand the operational lifecycle, not just initial setup.

---

# Part 9 — The endpoint toolbox

Do not memorize URLs blindly. Learn what each endpoint does and retrieve the real endpoints from discovery when possible.

| Endpoint | What you use it for |
|---|---|
| `/authorize` | Starts browser authorization/authentication and obtains an authorization code |
| `/token` | Exchanges a code, refresh token, or client credentials for tokens |
| `/userinfo` | Returns user claims allowed by the granted OIDC scopes using an access token |
| `/introspect` | Checks token active state remotely with Okta |
| `/revoke` | Revokes an access or refresh token |
| discovery endpoint | Publishes issuer metadata and supported endpoint locations |
| JWKS endpoint | Publishes public signing keys |
| logout/end-session path | Participates in OIDC/Okta sign-out behavior depending on the implementation |

## `/userinfo` — know why it exists

A common ticket sounds like:

> Login works, but the application cannot see the user's email/name/groups.

Do not immediately assume the login failed.

Ask:

```text
Which scopes were requested?
Which claims are configured in the ID token?
Is the application expecting the claim in /userinfo instead?
Is the access token appropriate for /userinfo?
Is the claim configured for this authorization server/token type?
```

Know the difference between:

- claims in the ID token
- claims returned by `/userinfo`
- claims/scopes in the access token used by the API

---

# Part 10 — Authorization servers, scopes, claims, audience, and policies

This is core Okta engineering knowledge.

## Scope

A permission requested by a client, for example:

```text
employee.read
salary.read
expense.approve
```

## Claim

A statement carried in a token or UserInfo response, for example:

```text
department = Finance
employeeType = Contractor
```

## Group

An Okta group membership, for example:

```text
FinanceManagers
HR
```

A group can be used as input to policy or represented in claims depending on the design. Do not confuse “group” with “scope.”

## Audience

Who the access token is intended for:

```text
api://employee-service
```

The API validates that it is the intended audience.

## Org Authorization Server vs Custom Authorization Server

| | Org Authorization Server | Custom Authorization Server |
|---|---|---|
| Typical issuer | `https://{yourOktaDomain}` | `https://{yourOktaDomain}/oauth2/{id}` |
| Main resource server | Okta | Your API |
| Okta API scopes | Yes | No |
| Custom API scopes | No | Yes |
| Custom API audience/access policies | No | Yes |
| App locally validates access token for its own API | No — treat org-AS access tokens as opaque | Yes |
| OIDC SSO | Yes | Yes |
| Typical use | OIDC SSO and Okta API access | Protecting your APIs |

Small nuance worth knowing: the Org Authorization Server can support some customization such as custom **ID-token claims**. That does not make it a custom API authorization server.

Operational note: Custom Authorization Servers require API Access Management in production Okta environments. Do not assume every customer tenant is licensed for it just because your lab tenant has it.

## How scope authorization actually works

Do not learn this incorrectly:

```text
User is in FinanceManagers
-> policy automatically inserts expense.approve
```

Learn this:

```text
Client requests expense.approve
        |
        v
Custom Authorization Server evaluates policies/rules
        |
        v
Matching rule permits that requested scope for this client/user/grant context
        |
        v
Token contains expense.approve
        |
        v
API checks expense.approve before POST /approve
```

Policies/rules act as an allowlist around the request. They are evaluated in priority order. The first applicable policy/rule is important, so rule order is a real troubleshooting concern.

## Do not mix the policy layers

This is a frequent source of confusion.

### Authorization Server Access Policy

Think **API/token authorization**:

- which client
- which grant type
- which user/group conditions where applicable
- which requested scopes are allowed
- access-token lifetime
- refresh-token lifetime
- rule order

### Global Session Policy + App Sign-In / Authentication Policy

Think **user authentication and assurance**:

- can the user establish an Okta session?
- is another factor required?
- what authentication assurance is required?
- when must the user reauthenticate?

If the symptom is “unexpected MFA prompt,” do not start by changing a Custom Authorization Server access policy.

If the symptom is “token request denied, wrong scopes, or wrong token lifetime,” inspect the authorization-server access policy.

## Custom claims and groups — implement this once

This is common enough in Okta work that you should configure it yourself rather than only understand the definition.

On a Custom Authorization Server, practice creating:

- one custom claim based on a user/profile attribute, such as `department`
- one groups claim with a sensible filter
- one claim included only when a particular scope is granted
- one claim in an access token and one in an ID token so you see the difference

Understand the settings that control:

```text
claim name
ID token vs access token
Expression vs Groups source
Okta Expression Language value
scope condition / include-in behavior
group filter
```

Use **Token Preview** while building claims, but still confirm the result with a real authorization flow. A preview proves the expression/configuration; the real flow proves the client, requested scopes, policy, and token behavior together.

A useful failure lab is:

> The user has `department=HR`, but the application cannot see `department`.

Check whether the claim is configured for the expected token type, whether its scope condition is satisfied, whether the client requested the needed scope, and whether the application is looking in the ID token, access token, or `/userinfo` response.

## Consent — recognize, do not over-study

A scope can be configured so user/admin consent affects authorization. If an unexpected consent screen appears, distinguish that from MFA and from an authorization-server policy denial. Learn enough to identify the layer; do not make consent configuration a large part of this course unless your project uses it heavily.

---

# Part 11 — Sessions, logout, refresh, and revocation

This deserves its own section because many real tickets come from treating all state as one thing.

Keep these separate:

```text
Okta browser session cookie
Application session
ID token
Access token
Refresh token
```

## Scenario 1 — App logout but Okta session remains

```text
User logs out of application
        |
        v
Local app session removed
        |
        v
Okta session may still exist
        |
        v
Next OIDC authorization can SSO the user back in
```

This explains “I logged out but I was signed straight back in.”

## Scenario 2 — Okta session ends but access token is still within lifetime

Do not assume deleting an interactive browser session magically changes every already-issued JWT at every API.

Your resource server's validation model matters.

- Local JWT validation checks cryptographic validity and claims/lifetime.
- Remote introspection can be used when current token active/revocation state is required.

## Scenario 3 — Access token expires but refresh token is valid

The application may obtain a new access token without an interactive login.

## `/revoke`

Know what revocation is used for and test it.

Important practical behavior in Okta:

- revoking an access token does **not** revoke the related refresh token
- revoking a refresh token also revokes its associated access token **at the authorization server**
- however, a resource server doing **local JWT validation** has no live revocation check; an already-issued JWT can continue to pass signature, issuer, audience, and lifetime validation until it expires
- if the API must detect revocation immediately, use **remote introspection** (or another design that checks current authorization-server state)
- revocation and browser-session termination are separate concepts

Do not memorize this only as text. Revoke tokens, then test the same token once with local JWT validation and once through `/introspect` so you can see the difference yourself.

## Logout lab

Prove the difference between:

1. application local logout
2. Okta/browser session logout
3. access-token expiry
4. refresh-token revocation
5. access-token revocation/introspection state

If you can predict the next user experience before running the test, you understand the lifecycle.

---

# Part 12 — The five integrations you should implement

These cover most day-to-day OAuth/OIDC engineering work.

## 1. Server-side web application login

```text
Browser
  |
  v
Web application
  |
  v
Okta
  |
  | authorization code
  v
Backend
  |
  | /token + client authentication + PKCE
  v
Tokens
```

Configure and understand:

- app type
- redirect URI
- client authentication
- PKCE
- issuer
- scopes
- ID-token validation
- application session
- logout

## 2. SPA integration

```text
Browser SPA
  |
  | Authorization Code + PKCE
  v
Okta
  |
  v
Access token
  |
  v
API
```

Learn practical browser problems:

- no client secret in JavaScript
- PKCE
- callback handling
- CORS/Trusted Origins when applicable
- cookies and browser restrictions
- token storage trade-offs
- refresh-token rotation
- “works in Postman, fails in browser”

## 3. Protected API

```text
Client
  |
  | access token
  v
API
  |
  +--> validate signature / issuer / audience / lifetime
  |
  +--> check required scope/claim
  |
  v
ALLOW or DENY
```

Test this matrix:

| Request | Expected reasoning |
|---|---|
| No token | 401-type authentication failure |
| Invalid/expired token | 401-type authentication failure |
| Valid token, required permission absent | 403-type authorization failure |
| Valid token, required permission present | request succeeds |

## 4. Machine-to-machine API integration

```text
Service A
  |
  | Client Credentials
  v
Okta Custom Authorization Server
  |
  | access token
  v
Service B API
```

No human user. No interactive login. No ID token.

Learn:

- client authentication
- service-specific scopes
- access policy
- token caching/renewal
- key/secret handling
- least privilege

## 5. Okta Management API automation

```text
Python / PowerShell / backend service
        |
        | private_key_jwt
        v
Okta Org Authorization Server /token
        |
        | scoped access token
        v
Okta Management API
```

Practice real calls such as:

- list users
- retrieve one user
- list groups
- create a test user
- add/remove test user from a group
- read application assignments

Understand all authorization layers:

```text
API service app
  + OAuth scopes granted to the app
  + admin role/resource access
  + private/public key pair
  + client assertion
  = allowed Okta API operations
```

Failure labs:

- missing OAuth scope
- scope present but insufficient admin role/resource access
- wrong private key
- wrong assertion audience
- expired assertion
- bad `kid`

---

# Part 13 — Project intake: what to ask before you implement

This is the checklist you should use in a real project meeting.

## Application shape

- SPA, native/mobile, server-side web app, API, background service, or combination?
- What framework/language is used?
- Who owns frontend, backend, API, and Okta configuration?

## User and access model

- Is there an end user in the flow?
- Workforce users, customers, partners, or service accounts?
- Is this authentication, API authorization, or both?
- Which users/groups should access the application?

## OAuth/OIDC design

- Redirect or embedded authentication?
- Which authorization server?
- Which flow/grant type?
- Which redirect and logout URIs for each environment?
- Which scopes are required?
- Which claims does the application actually need?
- What is the API audience?
- Does the application need refresh tokens?
- How should the client authenticate?

## API behavior

- Which API endpoints require which scopes/roles?
- How will access tokens be validated?
- Local JWT validation or introspection where current revocation state matters?
- Expected 401 vs 403 behavior?

## Authentication policy

- Existing Global Session Policy?
- Existing App Sign-In/Authentication Policy?
- MFA or authentication-assurance requirement?
- Existing routing/external IdP behavior that could affect login?

## Operations

- Dev/test/prod Okta orgs or apps?
- Who owns client secret/private key storage?
- Rotation requirement?
- Monitoring and System Log access?
- Change-management/promotion process?
- API Access Management licensing available if Custom Authorization Server is required?

This checklist keeps you from discovering architectural requirements halfway through implementation.

---

# Part 14 — Troubleshooting methodology

Never start by randomly changing settings. Locate the failed layer.

```text
1. App builds request
       |
2. Browser reaches /authorize
       |
3. User authentication / policy evaluation
       |
4. Authorization response / callback
       |
5. Authorization code returned
       |
6. Client calls /token
       |
7. Tokens issued
       |
8. Client validates OIDC response / ID token
       |
9. Client calls API with access token
       |
10. API validates token
       |
11. API authorizes operation
```

Ask first:

> What is the last step I can prove succeeded?

Then investigate the next step.

## `/authorize` problems

Look at:

- client ID
- issuer/authorization-server URL
- redirect URI
- response type
- requested scopes
- `state`
- `nonce`
- PKCE challenge
- app access/assignment
- authentication policy
- authorization-server policy when applicable
- error/error_description returned to callback

## Authentication/MFA problems

Look at:

- Global Session Policy
- App Sign-In/Authentication Policy
- authenticators
- existing Okta session
- routing / external IdP if relevant
- System Log

Do not confuse these with Custom Authorization Server access policies.

## `/token` problems

Look at:

- authorization code validity/reuse
- redirect URI equality
- PKCE verifier
- grant type
- client authentication method
- client secret/private key
- token endpoint/issuer
- requested/allowed scope

## API problems

Look at:

- access token actually present?
- wrong token type, such as ID token sent to API?
- issuer
- audience
- signature
- `kid` / JWKS refresh
- expiration / `nbf`
- system clock skew
- required scope/claim
- API's own authorization logic

## Browser-only problems

If Postman/curl works but browser does not, think about browser-specific layers:

- CORS
- Trusted Origins where applicable
- cookie behavior
- third-party cookie restrictions
- origin mismatch
- callback route handling
- PKCE state stored/lost in browser
- HTTPS/mixed-content issues

## Common symptom map

| Symptom | First areas to investigate |
|---|---|
| redirect URI error | Requested callback vs registered callback |
| `invalid_client` | Client ID, configured token auth method, secret/key/assertion |
| `invalid_grant` | Code expired/reused, redirect URI, PKCE verifier, refresh token state |
| `invalid_scope` | Requested scope, authorization server, access policy/allowed scope |
| no refresh token | `offline_access`, Refresh Token grant, policy/configuration |
| 401 from API | Token present? valid? correct issuer/audience/signature/lifetime? |
| 403 from API | Required scope/claim/permission missing |
| unknown `kid` | Wrong issuer/JWKS or key cache/rotation problem |
| audience mismatch | Wrong Custom AS/audience or wrong token used for API |
| unexpected MFA | Global Session/App Sign-In policy, not Custom-AS access policy |
| token missing expected scope | Was scope requested? Did access policy permit it? |
| login works, profile claim missing | requested scopes, ID token vs `/userinfo`, claim configuration |
| app logout immediately signs user back in | local session ended but Okta session still active |
| Postman works, SPA fails | browser/CORS/origin/cookie/PKCE/callback issue |
| works in dev, fails in prod | issuer, client ID, redirect URI, secret/key, policy, assignment, environment config |

## The explanation standard

Weak:

> The OAuth setting was wrong. I changed it and it worked.

Engineer-level:

> The browser authorization completed and the callback contained a valid code. The failure happened at `/token`, which returned `invalid_grant`. The redirect URI and client were correct, but the `code_verifier` did not correspond to the challenge sent on `/authorize`. After correcting the PKCE pair, the same flow returned tokens. The Network trace and System Log confirmed the failed and successful exchanges.

That is the habit this course is trying to build.

---

# Part 15 — Operational engineering you should know

You do not need to become a platform architect, but real projects continue after the first successful login.

## Environment separation

Treat dev, test, and production as separate configuration.

Expect different:

- client IDs
- secrets/keys
- redirect URIs
- logout URIs
- authorization-server issuers
- API audiences
- policies
- assignments

Do not copy a production secret into test or hardcode environment URLs into source code.

## Credential handling

Know these rules:

- never put a confidential client secret in a SPA/mobile app
- store backend secrets/private keys in an appropriate secret-management mechanism
- do not commit secrets/private keys to source control
- know who owns rotation
- test rotation before an emergency forces it

## JWKS/key rotation

Resource servers should use discovery/JWKS and a library that can refresh signing keys. Do not manually paste one signing certificate/key into application code and forget about it.

## SDKs vs protocol knowledge

In production you should normally use maintained OAuth/OIDC libraries or Okta-supported SDKs rather than implementing protocol details yourself.

You still need to understand the protocol because SDK errors eventually map back to:

```text
/authorize
/token
callback/state/nonce
issuer/JWKS
session
scope/claim
API authorization
```

Build requests manually during training so you understand them. Use supported libraries in real applications.

## Practical security rules — know these, skip the security-research rabbit hole

You do need the security habits that affect normal implementation work:

- use HTTPS; tokens and authorization codes are credentials, not harmless strings
- send access tokens in the Authorization header, not in URLs
- do not log access tokens, refresh tokens, client secrets, or private keys in production logs
- request only the scopes the client actually needs
- keep access tokens reasonably short-lived and use refresh mechanisms where appropriate
- protect refresh tokens because they can outlive access tokens
- validate redirect URIs and never use an open-ended redirect design
- validate issuer and audience rather than merely checking that a JWT can be decoded
- use discovery/JWKS and supported libraries instead of hand-rolled crypto
- give automation/service clients least-privilege scopes and admin roles

That is enough security depth for this course. Detailed attack research belongs later if your role or project requires it.

---

# The 15-day execution plan

Aim for roughly **2–3 focused hours per day**. More important than the clock: every day should include hands-on work.

## Day 1 — Core logic and architecture

Learn:

- authentication vs authorization
- OAuth vs OIDC
- actors
- public vs confidential clients
- frontend vs backend
- OIDC/OAuth vs SAML/SCIM boundaries

Do:

- take five application examples and classify them
- draw the actors for each

Break/fix:

- identify why “we need OAuth login and provisioning” is actually multiple requirements

## Day 2 — HTTP and the real transaction

Learn:

- redirects
- headers
- cookies
- query/form parameters
- bearer tokens
- 302/400/401/403

Do:

- capture an Okta sign-in in browser DevTools
- follow every redirect

Break/fix:

- change a callback route and identify the failed step

## Day 3 — Authorization Code + PKCE

Learn deeply:

- authorization request
- code exchange
- `state`
- `nonce`
- verifier/challenge
- confidential-client authentication + PKCE

Do:

- inspect or manually build the request

Break/fix:

- wrong verifier
- reused code
- wrong redirect URI

## Day 4 — Tokens and refresh

Learn:

- ID vs access vs refresh token
- `offline_access`
- expiry
- refresh rotation

Do:

- decode real tokens
- obtain and use a refresh token

Break/fix:

- missing `offline_access`
- expired access token
- revoked refresh token

## Day 5 — JWT validation and JWKS

Learn:

- header/payload/signature
- `kid`
- discovery
- JWKS
- issuer/audience/lifetime
- validation vs authorization

Do:

- validate a token using a standard library

Break/fix:

- wrong issuer
- wrong audience
- expired token
- unknown `kid`

## Day 6 — Okta application configuration and client authentication

Learn:

- app types
- redirect/logout URIs
- assignments/Controlled Access
- Trusted Origins
- `none`
- `client_secret_basic`
- `client_secret_post`
- `private_key_jwt`

Break/fix:

- `invalid_client`
- unassigned user
- wrong callback

## Day 7 — Web and SPA integrations

Implement both:

- server-side web application
- SPA using Authorization Code + PKCE

Compare:

- where tokens are held
- how `/token` differs
- browser-specific problems

## Day 8 — Protected API

Implement:

- bearer access token
- JWT validation
- scope-based authorization

Prove:

```text
no/invalid token -> authentication failure
valid token + missing permission -> authorization failure
valid token + permission -> success
```

## Day 9 — Authorization servers and policies

Learn deeply:

- Org vs Custom Authorization Server
- scope
- claim
- group
- audience
- access-policy rule order
- requested-then-permitted scope model
- authentication policies vs API access policies
- custom claims, group claims, and Token Preview

Do:

- create a `department` claim and a filtered groups claim
- verify which token/response contains each claim

Break/fix:

- wrong issuer
- wrong audience
- rule ordering
- requested scope not permitted

## Day 10 — Sessions, logout, UserInfo, revocation

Learn:

- Okta session vs app session
- `/userinfo`
- `/revoke`
- `/introspect`
- local logout vs Okta logout

Break/fix:

- “logout but immediately SSO back in”
- “login works but email/group claim is missing”
- revoked/expired token behavior

## Day 11 — Client Credentials and machine-to-machine

Implement:

- service app
- Custom AS
- service scope
- Client Credentials
- client authentication
- API call

Break/fix:

- invalid client credential
- wrong scope
- access-policy mismatch

## Day 12 — Okta API automation

Implement with Python or PowerShell:

- API Service app
- key pair
- `private_key_jwt`
- Okta API scopes
- admin role/resource assignment
- token acquisition
- real Okta API calls

Break/fix:

- wrong key/assertion
- missing scope
- missing admin permission

## Day 13 — Browser and authentication troubleshooting day

No new major concepts.

Diagnose deliberately broken cases:

- callback mismatch
- state/nonce issue
- CORS/origin issue
- assignment issue
- wrong issuer
- unexpected MFA
- browser cookie/session behavior

Use the three-source proof rule.

## Day 14 — Token/API/automation troubleshooting day

Diagnose:

- `invalid_client`
- `invalid_grant`
- `invalid_scope`
- 401
- 403
- wrong audience
- expired token
- unknown `kid`
- missing scope
- refresh failure
- Okta API scope vs admin-role problem
- dev works / prod fails

Again, prove every diagnosis.

## Day 15 — Capstone: work like the implementation engineer

Requirement:

> A company has a React frontend and a Java API. Employees authenticate through Okta. Only HR employees may read `/salary`. A scheduled backend process also needs API access without a human user. The application needs refresh support, clean logout behavior, and separate dev/prod configurations.

Design and build it without a step-by-step guide.

A clean first design:

```text
React SPA
  |
  | Authorization Code + PKCE
  v
Okta Custom Authorization Server
  |
  | access token with salary.read when permitted
  v
Java API
  |
  | validate token
  | require salary.read for GET /salary
  v
Protected data
```

Service path:

```text
Scheduled service
  |
  | Client Credentials
  v
Okta Custom Authorization Server
  |
  | service access token
  v
Java API
```

For the HR user path, keep the authorization model simple first:

```text
Client requests salary.read
        |
User is in HR and matching access-policy rule permits salary.read
        |
Access token contains salary.read
        |
Java API requires salary.read
```

After that works, learn the alternative of using a group/custom claim where the application design truly needs claim-based authorization.

Then deliberately break at least ten things and troubleshoot them without being told the category.

---

# Detailed mentor-led lessons — the actual teaching layer

The execution plan above tells you **what** to learn each day. This section is the part you actually study. Do not treat it as reading material to finish. Work through it with your Okta lab open, your browser Network tab open, and Postman or curl nearby.

For every day, use the same engineering habit:

```text
Understand the requirement
        ↓
Draw the actors and trust boundaries
        ↓
Trace the actual requests
        ↓
Configure both Okta and the application side
        ↓
Prove the happy path
        ↓
Break one thing deliberately
        ↓
Find the exact failed layer
        ↓
Prove the root cause from evidence
        ↓
Explain it in plain language
```

You do not need to memorize every screen or endpoint URL. You need to understand the logic well enough that, when a customer uses a different framework or the Okta UI moves, you can still reason your way through the integration.

---

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

## Day 3 — Authorization Code + PKCE: understand why every piece exists

### Start with the problem PKCE solves

Suppose the application starts an authorization flow and receives:

```text
https://app.example.com/callback?code=ABC123
```

The code is intentionally short-lived and one-time, but imagine another party manages to intercept it before the legitimate client redeems it.

If possession of the code alone were enough, the attacker could try:

```text
stolen code
   |
   v
/token
   |
   v
access token
```

PKCE adds a second piece that the legitimate client created before the authorization request.

### The verifier/challenge logic

The client generates a high-entropy random value:

```text
code_verifier = secret random value for this transaction
```

It derives:

```text
code_challenge = BASE64URL(SHA256(code_verifier))
```

The authorization request carries the challenge, not the verifier:

```text
Client/Browser -> Okta /authorize
                   code_challenge=...
                   code_challenge_method=S256
```

Later, the token request sends the verifier:

```text
Client -> Okta /token
          code=ABC123
          code_verifier=<original value>
```

Okta derives the challenge from that verifier and compares it with what was bound to the authorization request.

```text
SHA256(received code_verifier)
             ==
original code_challenge ?
```

If not, the code cannot be redeemed through that PKCE transaction.

The point is not to memorize a hash formula. The point is:

> The authorization code is not enough by itself. The client must also prove possession of the verifier created for that flow.

### Understand `state` separately

`state` is not PKCE.

The application generates a value before redirecting to Okta and expects the same value back.

```text
App creates state = X
        ↓
/authorize?...state=X
        ↓
callback?...state=X
        ↓
App compares expected vs returned
```

That helps bind the browser response to the browser transaction the application initiated and protects against request-forgery style problems.

If the application generated `state=A` but receives `state=B`, do not continue just because a valid-looking code is present.

### Understand `nonce` separately

`nonce` belongs to the OIDC identity side.

The client sends it in the authorization request. The resulting ID token should be tied back to that request through the nonce value.

Think:

```text
state → protect/correlate authorization response transaction
nonce → bind OIDC ID-token response to authentication request
PKCE  → protect authorization-code redemption
```

They are related to the same flow but solve different problems.

### The full flow

```text
1. Client generates state, nonce, code_verifier
2. Client derives code_challenge
3. Browser -> Okta /authorize
4. User authenticates
5. Okta evaluates policies/authorization request
6. Okta -> browser -> callback?code=...&state=...
7. Client verifies state
8. Client -> /token with code + code_verifier
9. Confidential client also authenticates itself if configured
10. Okta returns applicable tokens
11. Client validates the OIDC response/ID token
```

### Public and confidential clients

For a SPA:

```text
client authentication = none
PKCE                  = yes
```

For a confidential web app:

```text
client authentication = client secret/private key
PKCE                  = also usable/recommended
```

Do not think client authentication and PKCE are substitutes.

```text
client authentication → proves the client identity
PKCE                  → binds code redemption to the initiating client transaction
```

### Build the request manually once

Use an SDK in production, but during training inspect or manually construct:

```http
GET https://{yourOktaDomain}/oauth2/default/v1/authorize?
 client_id=...
 &response_type=code
 &redirect_uri=http://localhost:3000/callback
 &scope=openid%20profile%20email
 &state=...
 &nonce=...
 &code_challenge=...
 &code_challenge_method=S256
```

After the callback, inspect:

```text
code
state
```

Then inspect the token request.

### Break/fix labs

Break one at a time:

**Wrong verifier**

Expected reasoning:

```text
/authorize succeeded
callback contains code
/token fails
→ investigate code redemption/PKCE
```

**Reused authorization code**

First exchange succeeds, second fails.

**Wrong redirect URI at token exchange**

The URI must stay consistent with the authorization transaction where required.

**Wrong `state`**

The client should reject the browser response rather than blindly continuing.

**Wrong `nonce`**

The OIDC response should fail the client's nonce validation.

### Explain-back checkpoint

You should be able to explain PKCE without saying “because OAuth requires it.” Explain the attack/problem first, then the mechanism.

---

## Day 4 — Tokens: know what each one is for and how its lifecycle works

### Start with three different consumers

A common beginner mistake is treating every token as “the OAuth token.” Stop doing that now.

```text
ID token      → client application
Access token  → resource server/API
Refresh token → authorization server
```

The easiest way to understand them is to ask:

> Who is supposed to consume this token, and what question are they trying to answer?

### ID token

The application wants to know about the authentication event/user.

A simplified payload might contain:

```json
{
  "iss": "https://example.okta.com/oauth2/default",
  "sub": "00u123...",
  "aud": "0oaClientId...",
  "exp": 1780000000,
  "iat": 1779996400,
  "nonce": "...",
  "email": "user@example.com"
}
```

Notice the audience: for an ID token, the client application is the intended audience.

### Access token

The API needs a credential representing granted access.

The client sends it like this:

```http
GET /api/profile
Authorization: Bearer eyJ...
```

For an access token minted by a Custom Authorization Server for your API, the API validates it and then checks the appropriate scopes/claims.

Never build an API that accepts an ID token just because “it is also a JWT.” Correct token type and audience matter.

### Refresh token

Access tokens should not need to live forever just so the user avoids signing in every hour.

The refresh token solves that lifecycle problem:

```text
Access token expires
        ↓
Client sends refresh token to /token
        ↓
New access token
        ↓
Possibly new refresh token when rotation is used
```

The refresh token is powerful precisely because it can outlive an access token. Treat it as a sensitive credential.

### `offline_access` — understand what it does

If an Authorization Code/OIDC client needs refresh-token capability, request:

```text
offline_access
```

in the authorization request, assuming the app and policy are configured to permit refresh tokens.

A typical scope set could be:

```text
openid profile email offline_access employee.read
```

Do not assume that checking “Refresh Token” in the app configuration automatically means every authorization response will contain one.

### Refresh-token rotation

With rotation, the client uses refresh token R1:

```text
R1 -> /token -> access token A2 + refresh token R2
```

Now R2 is the token to keep using. Reuse of an old rotating token can indicate replay/compromise and trigger Okta's reuse-detection behavior.

The important engineering lesson is not to memorize every lifetime. Learn where lifetimes and rotation are configured and how your client library handles token replacement.

### Client Credentials is different

For a machine-to-machine Client Credentials integration, there is no user session to extend. The service normally requests a new access token when the existing one expires.

Think:

```text
service credential
      ↓
/token grant_type=client_credentials
      ↓
short-lived access token
      ↓
cache until near expiry
      ↓
request another access token
```

Do not design M2M around the user refresh-token pattern.

### Inspect real tokens

Decode a real ID token and Custom-AS access token. Find:

```text
iss
sub
aud
exp
iat
scp
kid (header)
```

Do not interpret a claim just because you recognize its name. Ask what component is expected to consume that token.

### Break/fix labs

1. Remove `offline_access` and observe the token response.
2. Let an access token expire and call the API again.
3. Use the refresh token to obtain another access token.
4. Enable/use rotation and inspect the refresh-token replacement behavior.
5. Revoke the refresh token and test what happens next.

### Explain-back checkpoint

You should be able to answer:

> Why not just make the access token valid for a week?

A good answer talks about limiting exposure, short-lived API credentials, and using the refresh lifecycle when continued access is appropriate.

---

## Day 5 — JWT validation, discovery, JWKS, and why “it decodes” proves almost nothing

### Decoding is not validation

Anyone who has a JWT string can base64url-decode its header and payload.

That does **not** prove:

```text
who issued it
whether it was modified
whether it is for your API
whether it is expired
whether the signing key is trusted
```

So this is a bad security check:

> “I pasted the token into a decoder and it looked correct.”

### Understand the JWT shape

```text
header.payload.signature
```

Header:

```json
{
  "alg": "RS256",
  "kid": "abc123"
}
```

Payload:

```json
{
  "iss": "https://example.okta.com/oauth2/default",
  "aud": "api://employee-service",
  "sub": "00u...",
  "exp": 1780000000,
  "scp": ["employee.read"]
}
```

Signature: the part that lets the verifier detect alteration and confirm the token was signed by a trusted authorization server key.

You do not need the RSA mathematics. You need the trust chain.

### Discovery gives the client/API metadata

Start from the issuer you trust.

Conceptually:

```text
configured issuer
      ↓
OIDC discovery document
      ↓
authorization_endpoint
      token_endpoint
      jwks_uri
      userinfo_endpoint
      ...
```

The lesson is important: **configure the issuer and discover the related endpoints/keys** rather than mixing endpoints from different authorization servers or domains.

### JWKS and `kid`

Okta publishes public keys in a JWKS document.

```text
JWT header kid
      ↓
find matching JWK
      ↓
verify JWT signature
```

Libraries should cache keys and refresh them when required. If an application hardcodes one signing key forever, signing-key rotation eventually creates an `unknown kid` or signature failure.

### Validation logic

Think in this order:

```text
1. Is this structurally a token I can parse?
2. Is the signature valid with a trusted current key?
3. Is iss exactly the authorization server I trust?
4. Is aud the API/resource I am protecting?
5. Is exp still valid?
6. Is nbf valid if present?
7. Is the expected signing algorithm allowed?
```

Only then:

```text
8. Does the token contain the permission this endpoint requires?
```

Step 8 is authorization, not cryptographic token validation.

### 401 vs 403 working rule

```text
Token missing / cannot be trusted / expired
→ authentication credential unacceptable
→ typically 401

Token valid, but salary.read missing
→ caller is known/accepted but not authorized for this operation
→ typically 403
```

Use framework behavior as evidence, but keep the conceptual distinction.

### Local validation vs introspection

Local JWT validation:

```text
API
  ↓
verify JWT using cached/public keys and claims
  ↓
no network call to Okta per request
```

Introspection:

```text
API/backend
  ↓
/introspect at Okta
  ↓
current active state
```

Introspection can provide current authorization-server state, including revocation awareness, at the cost of a remote dependency/call.

### Org AS warning

Do not locally build your own API authorization around Org Authorization Server access-token contents. Those tokens are for Okta. Treat them as opaque from your application's perspective.

For your own API, use a Custom Authorization Server designed for that resource server.

### Break/fix labs

- Change expected issuer.
- Change expected audience.
- Use an expired token.
- Modify the JWT payload manually and try validation.
- Simulate/use the wrong JWKS/issuer.
- Observe behavior when the verifier sees an unknown `kid`.

For each, do not just note “validation failed.” Record **which check failed**.

### Explain-back checkpoint

You should be able to explain:

> A JWT decoder only shows me contents. Trust comes from signature validation plus issuer, audience, and lifetime checks. After the token is trusted, the API still has to make a separate authorization decision.

---

## Day 6 — Okta application configuration and client authentication

### Stop treating the Okta app screen as a checklist

Every field exists because it changes protocol behavior or who is allowed to use the integration.

Before creating the app, know the architecture.

### Application type

If you choose SPA for something that is really a confidential backend, or Web for browser-only JavaScript, you can end up with the wrong client-authentication assumptions.

Map the runtime first:

```text
SPA       → public client
Native    → public client
Web       → usually confidential server-side client
API Service → confidential service client
```

### Client ID

The client ID is an identifier, not a secret.

It appears openly in authorization requests. Do not waste effort “hiding” a client ID.

### Redirect URI

The redirect URI is a security boundary. Okta should return an authorization response only to a registered location.

Real mistakes:

```text
http vs https
localhost:3000 vs localhost:3001
/callback vs /login/callback
/test callback used in prod
custom domain URL mixed with org domain assumptions
```

Treat it as exact configuration, not a friendly destination label.

### Assignments / Controlled Access

If the app is restricted to assigned users/groups, assignment is part of the authorization to use the application.

But do not blindly tell every unassigned-login ticket “assign the user.” First check whether the app is configured for assigned access or everyone in the org.

System Log is valuable because it tells you why Okta denied the transaction.

### Trusted Origins and CORS

Use this working rule:

```text
Browser JavaScript making cross-origin request
→ browser enforces origin/CORS rules
→ Okta Trusted Origins may matter depending on operation

Backend server making HTTP request
→ browser CORS policy is not involved
```

This is why “Postman works, browser fails” is such a useful clue.

### Client authentication methods

#### `none`

Public client. No protected client credential.

Common with SPA/native Authorization Code + PKCE.

#### `client_secret_basic`

The secret is sent in HTTP Basic authentication to `/token`:

```http
Authorization: Basic base64(client_id:client_secret)
```

#### `client_secret_post`

The credential goes in the form body.

The client and Okta must agree on the configured method.

#### `private_key_jwt`

The client proves possession of a private key by signing a short-lived client assertion.

Conceptually:

```text
private key stays with client
       ↓
sign client assertion JWT
       ↓
/token request carries assertion
       ↓
Okta verifies against registered public key
```

Important fields:

```text
iss = client_id
sub = client_id
aud = exact token endpoint being authenticated to
exp = short-lived
kid = registered public-key identifier where applicable
```

Do not write signing crypto from scratch. Use maintained libraries. But know enough to diagnose the assertion.

### `invalid_client` is not one cause

When `/token` says `invalid_client`, check:

```text
correct client_id?
correct token endpoint?
correct auth method?
secret current/correct?
Basic vs POST mismatch?
private key matches registered public key?
kid correct?
assertion audience exact?
assertion expired?
```

### Rotation is part of implementation

A project is not complete because today's secret works.

Ask:

```text
Who owns the secret/key?
Where is it stored?
How is it rotated?
Can old/new keys overlap during rotation?
How does deployment receive the new credential?
What monitoring tells us rotation broke authentication?
```

### Lab

Create one public OIDC app and one confidential web/service app. Compare their settings side by side.

Then intentionally make the client authentication method mismatch what the client sends and prove why `/token` fails.

---

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

## Day 8 — Protect the API: validation first, authorization second

### Start from the API's perspective

The API receives:

```http
GET /salary
Authorization: Bearer eyJ...
```

The API does not care that the browser previously showed an Okta login page. It cares whether this request contains an acceptable access token and whether that token grants this operation.

### Step 1 — authenticate/validate the credential

```text
Bearer token present?
        ↓
Signature valid?
Issuer expected?
Audience is this API?
Not expired / nbf valid?
        ↓
Token trusted
```

If the token is not trusted, stop.

### Step 2 — authorize the operation

Now ask:

```text
GET /employee/profile
requires employee.read

GET /salary
requires salary.read
```

The API should enforce the permission. Do not rely on the frontend hiding a button.

### Scope vs claim

Use scopes primarily to represent API permissions:

```text
employee.read
salary.read
expense.approve
```

Claims can carry contextual facts:

```text
department = HR
employeeType = Employee
groups = [...]
```

A project can authorize with scopes, claims, roles, or a combination, but keep the responsibility clear.

A clean first design for this course:

```text
client requests salary.read
Okta policy permits it only in the intended conditions
access token contains salary.read
API checks salary.read
```

Do not overcomplicate the first implementation with five different authorization models.

### The test matrix

Run all four intentionally:

```text
No token
→ fail

Garbage/expired/wrong-audience token
→ fail token validation

Valid token without salary.read
→ token trusted, operation denied

Valid token with salary.read
→ request allowed
```

Record the HTTP status and API logs for each.

### The API should log useful diagnostics without leaking credentials

Good logs:

```text
request correlation ID
validation reason category
issuer/audience mismatch
expired token
missing required scope
```

Bad logs:

```text
full access token
refresh token
client secret
private key
```

### Break/fix

1. Send the ID token instead of the access token.
2. Send an access token from the wrong authorization server.
3. Change the configured audience.
4. Remove `salary.read`.
5. Let the token expire.

For every failure, answer:

> Did the API reject the token itself, or accept the token and reject the requested operation?

That is the 401/403 reasoning you need in real support work.

---

## Day 9 — Authorization servers, scopes, claims, audience, and policy layers

### Why this day matters

Many Okta OAuth problems come from putting a correct configuration in the **wrong layer**.

You need a clean picture of who controls what.

### Org Authorization Server vs Custom Authorization Server

Think in terms of the resource server.

```text
Who will consume the access token?
```

If the answer is **Okta Management APIs**, use the Org Authorization Server with Okta API scopes.

If the answer is **your own API**, use a Custom Authorization Server so you can define the audience, custom API scopes/claims, and API access policies.

Do not select `/oauth2/default` because a tutorial did. Select the authorization server because you understand which resource is being protected.

### Audience

The audience is the resource server the access token is meant for.

Example:

```text
api://employee-service
```

The Employee API checks that value because a valid token for some other resource should not automatically be accepted here.

### Scope

A scope represents requested access.

```text
employee.read
salary.read
```

The client requests it.

### Access policy rule

The Custom Authorization Server decides whether that request is allowed under the matching policy/rule.

Correct working rule:

```text
Client requests salary.read
        ↓
Authorization Server evaluates policy/rule
        ↓
Rule permits requested salary.read under these conditions
        ↓
Token contains salary.read
```

Do not learn:

```text
HR group automatically inserts salary.read
```

unless you deliberately configured some separate/default behavior that makes that true. Your base rule is requested → evaluated → permitted.

One practical exception to recognize: Okta custom scopes can be configured as **default scopes**. If a client omits the `scope` parameter, permitted default scopes can be included according to configuration/policy. Treat that as explicit authorization-server configuration, not as a group magically injecting permissions.

### Rule ordering matters

Policies and rules are evaluated in priority order. The first matching policy/rule can determine the result.

That creates real tickets:

> “My group-specific rule looks correct, but it never applies.”

Ask whether an earlier broader rule matched first.

### Claims

Claims are information carried in tokens/UserInfo.

Examples:

```text
department = HR
groups = [HR, Employees]
```

Configure a claim once with:

```text
claim name
ID token vs access token
Expression or Groups source
scope condition
filter
```

Use Token Preview to debug the expression/configuration, but confirm with a real flow because the real flow also tests requested scopes, client, policy, and token type.

### Do not mix API policy and MFA policy

This distinction needs to become automatic.

```text
Custom Authorization Server Access Policy
→ client/grant/requested scopes/user conditions/token lifetime/rule order

Global Session Policy + App Sign-In/Authentication Policy
→ user authentication/session/MFA/assurance/reauthentication
```

Unexpected MFA?

Start in authentication/session policy, not Custom-AS access policy.

Missing API scope or unexpected token lifetime?

Start in the authorization-server access policy.

### Lab

Build:

```text
Custom AS audience = api://employee-service
scope = salary.read
claim = department
policy/rule = allows intended client/users to request salary.read
```

Then break:

- rule order
- group condition
- requested scope
- issuer
- audience
- claim include-in condition

Use Token Preview and a real flow to see the difference.

---

## Day 10 — Sessions, logout, UserInfo, revocation, and the “why did it sign me back in?” ticket

### Separate all the state first

Keep this picture in your head:

```text
Okta browser session
Application session
ID token
Access token
Refresh token
```

They can influence one another, but they are not one object.

### Scenario: local app logout

The app deletes its local session:

```text
App session gone
```

But the browser may still have a valid Okta session.

Next time the app redirects to Okta:

```text
Browser -> Okta /authorize
Okta sees valid session
Okta does not need credentials again
Browser returns to app
```

The user says:

> I logged out and it logged me right back in.

Nothing mystical happened. The application session ended; the Okta SSO session did not.

### Scenario: Okta session ends

Ending the Okta browser session does not reach out and erase every JWT already issued to every API.

If a resource server is doing local JWT validation and the access token is still cryptographically valid and unexpired, it can continue to pass those local checks.

That is why session termination and token revocation/lifetime are separate concerns.

### `/userinfo`

Suppose login works but the app says the user's email is missing.

Do not jump to “authentication failed.”

Ask:

```text
Was email scope requested?
Is email expected in ID token?
Is the app expecting it from /userinfo?
Does the access token authorize /userinfo?
Is the claim configured for the token/response type?
```

The `/userinfo` endpoint is an OIDC way for the client to obtain allowed user claims using the appropriate access token.

### `/revoke`

Use revocation to tell the authorization server that a token should no longer be active.

Important behavior to understand:

```text
revoke access token
→ does not automatically revoke the related refresh token

revoke refresh token
→ associated access-token authorization is revoked at Okta
```

But if the API only performs local JWT validation, it does not call Okta to ask whether revocation occurred. An already-issued JWT can still pass local signature/issuer/audience/lifetime checks until expiration.

If immediate revocation awareness matters, introspection or another current-state design is needed.

### `/introspect`

Introspection asks the authorization server whether the token is currently active.

```text
local validation
→ fast, no Okta call for every request
→ no live revocation lookup

introspection
→ asks Okta current active state
→ network dependency/cost
```

You choose based on requirements, not because one is always universally better.

### Lab

Perform these separately:

1. Local app logout only.
2. Full Okta/browser sign-out.
3. Let access token expire.
4. Revoke access token.
5. Revoke refresh token.
6. Test the same revoked access token with local JWT validation.
7. Test it with `/introspect`.
8. Call `/userinfo` before and after changing scopes/claims.

If you can predict each result before running it, you understand the lifecycle.

---

## Day 11 — Client Credentials: machine-to-machine without pretending there is a user

### Start with the requirement

> Every night, Service A needs to call the Reporting API. No human is involved.

Do not force a user login into this architecture.

This is a client acting as itself.

```text
Service A
   |
   | authenticates as OAuth client
   v
Okta /token
   |
   | access token
   v
Service A
   |
   | Bearer access token
   v
Reporting API
```

### What is intentionally missing

```text
No browser
No interactive login
No Okta user session
No ID token
```

That absence is part of the design.

### Token request logic

Conceptually:

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&scope=report.read
```

plus the configured client authentication method.

The authorization server verifies the client and whether the requested scope is allowed for that service client/policy.

### Protect your API with service-specific permissions

Do not give a background job a broad `api.full_access` scope because it is convenient.

Prefer:

```text
report.read
job.execute
inventory.sync
```

that match what the service actually needs.

### Token caching and renewal

Do not carry the user refresh-token pattern into Client Credentials. A service normally obtains another access token by authenticating again with its client credentials when renewal is needed; do not expect an interactive-user refresh lifecycle here.

Do not request a fresh access token before every single API call if one valid token can safely be reused for its lifetime.

A service usually does:

```text
Get token
Cache securely
Use until near expiry
Request new access token
```

Build sensible retry behavior around token acquisition, but do not create an infinite retry loop when credentials are wrong.

### Secret/key operations are part of the integration

For M2M, ask:

```text
Where is the secret/private key stored?
Who rotates it?
What happens during rotation?
How is a failed token acquisition alerted?
What is the blast radius of this client?
```

### Break/fix

- wrong client secret/key
- wrong token endpoint
- wrong scope
- access-policy rule does not allow this client/grant/scope
- service uses expired access token without renewing
- API expects different audience

Explain each from the service's perspective, not the user's perspective, because there is no user.

---

## Day 12 — Automate Okta Management APIs with an OAuth service app

### Why this deserves its own day

Calling **your API** with Client Credentials and calling **Okta Management APIs** with an Okta OAuth service app are related but not identical configurations.

For Okta Management API access:

```text
Automation
   |
   | private_key_jwt client authentication
   v
Okta Org Authorization Server /token
   |
   | access token with Okta API scopes
   v
Okta Management API
```

### Why the Org Authorization Server

The resource server is Okta itself.

Therefore the access token needs Okta API scopes such as:

```text
okta.users.read
okta.users.manage
okta.groups.read
...
```

Those are minted by the Org Authorization Server, not your Custom Authorization Server.

### `private_key_jwt`

For the OAuth API Service app pattern, the client signs a short-lived assertion with its private key.

High-level flow:

```text
Generate/register public-private key pair
        ↓
Keep private key with automation
        ↓
Build short-lived client assertion
        ↓
Sign assertion with private key
        ↓
POST /oauth2/v1/token
        ↓
Okta verifies with registered public key
```

Typical token request includes:

```text
grant_type=client_credentials
scope=okta.users.read ...
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
client_assertion=<signed JWT>
```

### Scopes are necessary but not the whole permission model

This is a critical Okta implementation detail.

```text
OAuth scope
+
Admin role/resource assignment
=
actual Management API capability
```

A service app can have the scope string but still lack the admin role/resource permission required for the operation.

That creates a very important troubleshooting branch:

```text
Did token acquisition fail?
OR
Did token acquisition succeed but Management API authorization fail?
```

Do not solve the second problem by repeatedly rebuilding the client assertion.

### Lab

Use Python or PowerShell to:

1. Obtain the access token.
2. List users.
3. Read one test user.
4. List groups.
5. Add/remove a test user from a test group if your lab permits it.

Log only safe metadata:

```text
HTTP status
request correlation IDs where available
scope names
operation
```

Do not dump the private key or full tokens into normal logs.

### Break/fix

1. Sign with wrong private key.
2. Use wrong `kid`.
3. Use wrong assertion `aud`.
4. Expire the assertion.
5. Request an ungranted OAuth scope.
6. Grant the scope but remove/limit admin role resource access.

Your explanation should distinguish **client authentication**, **scope grant**, and **admin authorization** as separate layers.

---

## Day 13 — Browser and authentication troubleshooting: work from evidence

### No new major protocol concepts today

Today you train the support skill.

The rule is:

> What is the last step I can prove succeeded?

Use the three-source proof whenever available:

```text
Network/Postman/curl
+
Token inspection
+
Okta System Log
```

### Case 1 — Redirect URI mismatch

Symptoms might include an error before the application receives an authorization code.

Prove:

```text
Exact redirect_uri sent in /authorize
vs
Exact redirect URI registered in Okta
```

Do not say “callback issue” until you compare the actual strings.

### Case 2 — User is not allowed to the app

Check:

```text
Controlled Access model
Assignments/groups
System Log denial reason
```

Do not assume every app requires explicit assignment if it is configured for broader org access.

### Case 3 — Unexpected MFA

Do not start changing Custom Authorization Server access policies.

Investigate:

```text
Global Session Policy
App Sign-In / Authentication Policy
authenticator enrollment/state
existing session context
routing/external IdP if relevant
System Log policy evaluation
```

### Case 4 — State/nonce failure

Separate them.

```text
state mismatch
→ browser authorization transaction correlation/security

nonce mismatch
→ OIDC response/ID-token binding
```

Check whether application storage/state was lost during redirects.

### Case 5 — Works in Postman, fails in SPA

That clue makes server-side OAuth configuration less likely to be the entire problem.

Check:

```text
browser origin
CORS
Trusted Origins
cookie restrictions
callback route
HTTPS/mixed content
PKCE/state storage
```

### Case 6 — Login loop

Draw the loop.

```text
App -> Okta -> App -> Okta -> App ...
```

Then ask at the application callback:

```text
Did callback get a code?
Did /token succeed?
Did app create local session?
Did it immediately decide user is unauthenticated again?
```

Sometimes the OAuth flow is succeeding and the application-session layer is broken.

### Your output for every case

Write a short engineer incident note:

```text
Observed symptom:
Last confirmed successful step:
First failed step:
Evidence:
Root cause:
Configuration/code change:
Proof after change:
```

That format is more valuable than memorizing a list of error codes.

---

## Day 14 — Token, API, and automation troubleshooting

### Case 1 — `invalid_client`

Work the client-authentication layer:

```text
client ID
configured auth method
secret/key
kid
assertion aud
assertion exp
endpoint
```

Do not waste time debugging user MFA for a service-client `invalid_client` error.

### Case 2 — `invalid_grant`

First identify the grant you are using.

For Authorization Code:

```text
code expired/reused?
redirect URI mismatch?
PKCE verifier wrong?
wrong client/transaction?
```

For refresh:

```text
refresh token revoked/expired?
rotation/reuse issue?
wrong client?
```

The same error name can have different causes because different grants use different credentials.

### Case 3 — `invalid_scope`

Ask:

```text
Which authorization server?
Does that scope exist there?
Was the scope requested in the right place?
Does the client/policy permit it?
For Okta API service app, is the Okta API scope granted to the app?
```

### Case 4 — API 401

Use a validation checklist:

```text
Bearer token actually present?
Correct token type?
Correct issuer?
Correct audience?
Signature valid?
Token expired/not-before valid?
JWKS current?
```

### Case 5 — API 403

If token validation succeeded, move to permission:

```text
required scope present?
required claim/role present?
API's own authorization logic correct?
```

### Case 6 — unknown `kid`

Likely branches:

```text
wrong issuer / wrong JWKS
key rotation and stale cache
hardcoded key
malformed token header
```

Do not “fix” key rotation by permanently disabling signature validation.

### Case 7 — Dev works, prod fails

Compare environment by environment:

```text
issuer
authorization server ID
client ID
redirect URI
logout URI
secret/key
scope existence
access policy
assignment
audience
custom domain
CORS/Trusted Origin
```

This is why environment configuration belongs to engineering, not only deployment teams.

### Case 8 — Okta API token obtained, operation still denied

Separate:

```text
OAuth scope in token
vs
admin role/resource authorization
```

If scope is present but the service app is not authorized for that resource/action, rebuilding the JWT assertion does not fix the permission layer.

### Final troubleshooting drill

Have someone give you ten failures without telling you the category. For each, your first response should not be a fix. It should be:

> Show me the request/response at the failing step and the relevant System Log event.

Then reason from evidence.

---

## Day 15 — Capstone: operate like the implementation engineer

### Requirement

You are given only this:

> We have a React frontend and a Java API. Employees authenticate with Okta. Only HR employees should read `/salary`. A scheduled backend job also needs API access with no user. We need refresh support, clean logout, dev and prod, and the operations team wants automation against Okta Management APIs later.

Do not immediately open the Okta Admin Console.

### Step 1 — Break the requirement into trust relationships

```text
Employee -> React SPA -> Okta
React SPA -> Java API
Scheduled service -> Java API
Automation service -> Okta Management API
```

These are four different relationships.

### Step 2 — Classify clients/resources

```text
React SPA        = public OIDC/OAuth client
Java API         = resource server
Scheduled job    = confidential M2M client
Okta automation  = OAuth API Service app
```

### Step 3 — Choose flows

User path:

```text
Authorization Code + PKCE
```

Service path:

```text
Client Credentials
```

Okta Management automation:

```text
Client Credentials + private_key_jwt against Org AS
```

### Step 4 — Choose authorization server

For the Java API:

```text
Custom Authorization Server
Audience = resource identifier for Java API
```

For Okta Management APIs:

```text
Org Authorization Server
```

### Step 5 — Design the permission

Keep the first design simple:

```text
scope = salary.read
```

User flow:

```text
React requests salary.read
        ↓
Custom-AS rule evaluates intended conditions (including HR where designed)
        ↓
Token gets salary.read when permitted
        ↓
Java API validates token
        ↓
GET /salary requires salary.read
```

Then later compare a claim-based/group-based authorization design and explain why you would or would not choose it.

### Step 6 — Design refresh/logout

```text
React authorization request includes offline_access when refresh is required
Refresh-token rotation configured/understood
Local app logout defined
Okta sign-out behavior defined
Token revocation behavior understood
```

Do not promise that “logout instantly kills every JWT everywhere” unless the design actually enforces current revocation state.

### Step 7 — Design the service path

```text
Scheduled service
   |
   | Client Credentials + service-specific scope
   v
Custom AS
   |
   | access token
   v
Java API
```

Decide whether the service needs `salary.read` or a separate scope that more precisely describes the job's permission.

### Step 8 — Design environments

Create a table before implementation:

| Setting | Dev | Prod |
|---|---|---|
| Okta org/domain | | |
| client IDs | | |
| redirect URIs | | |
| logout URIs | | |
| Custom AS issuer | | |
| API audience | | |
| secrets/keys | | |
| assignments | | |
| policy/rules | | |
| Trusted Origins | | |

This prevents accidental cross-environment configuration.

### Step 9 — Build the happy path

Do not call it complete until you can show:

```text
User login succeeds
Correct ID token reaches client
Correct access token reaches API
API validates token
HR permission succeeds
non-HR permission fails as designed
refresh works
logout behaves as designed
service client calls API successfully
```

### Step 10 — Break at least ten things

Suggested failures:

1. Wrong redirect URI.
2. Wrong issuer.
3. Wrong audience.
4. Wrong PKCE verifier.
5. Missing `offline_access`.
6. Missing requested scope.
7. Access-policy ordering problem.
8. API receives ID token instead of access token.
9. CORS/origin failure.
10. Expired access token.
11. Revoked refresh token.
12. Wrong M2M client credential.
13. Wrong service scope.
14. Stale/wrong JWKS.
15. Prod client accidentally points at dev issuer.

For each, produce the same incident note:

```text
Observed symptom
Last successful step
First failed step
Evidence from Network/Postman/curl
Evidence from token
Evidence from System Log
Root cause
Fix
Proof after fix
```

### Step 11 — Explain the design to three audiences

**Application owner** — no protocol jargon unless necessary.

**Developer** — endpoints, tokens, callbacks, scopes, validation.

**Security/IAM engineer** — trust boundaries, client authentication, token lifecycle, policy, least privilege, rotation, logging.

If you can change your explanation without changing the underlying facts, you understand the system.

### Final engineer standard

At the end of Day 15, you should be able to receive an unfamiliar OAuth/OIDC ticket and do this:

```text
Identify architecture
      ↓
Identify expected flow
      ↓
Identify expected issuer/client/resource
      ↓
Locate failed transaction
      ↓
Inspect request/response
      ↓
Inspect token when one exists
      ↓
Inspect Okta System Log
      ↓
Determine the failing layer
      ↓
Fix only that layer
      ↓
Prove the behavior changed
```

That is the working confidence this course is designed to build. You will still look up vendor/version-specific details. That is normal engineering. The skill is knowing **what to look up, where it fits, and how to prove whether it is the cause**.

---

# How to study the detailed lessons without turning them into another reading exercise

Use this rule for every day:

```text
Read one concept
→ stop
→ draw it from memory
→ find it in a real request/configuration
→ explain it out loud
→ continue
```

At the end of each day, close the file and answer five questions from memory:

1. What problem did today's mechanism solve?
2. Which component sends what to whom?
3. What configuration exists on the Okta side?
4. What configuration/code exists on the application/API side?
5. What are the first three failure modes I would investigate?

If you cannot answer those without reopening the notes, repeat the relevant lab. The goal is not to finish all pages in 15 calendar days. The goal is for the logic to become natural enough that you can use it under project pressure.

---

# Engineer confidence checklist

Before you call yourself comfortable with OAuth/OIDC in Okta, you should be able to answer or demonstrate these without guessing.

## Architecture

- I can look at an application and classify each OAuth client.
- I can tell whether there is a user in the flow.
- I can choose Auth Code + PKCE vs Client Credentials.
- I know when I need Org AS vs Custom AS.
- I know OIDC/OAuth does not replace provisioning/SCIM.

## Authorization Code/OIDC

- I can draw the whole browser-to-token flow from memory.
- I can explain `state`, `nonce`, code, verifier, and challenge.
- I can explain why a public client cannot rely on a secret.
- I can explain why a confidential client may use both client authentication and PKCE.
- I know how `offline_access` relates to refresh tokens.

## Tokens

- I know who consumes ID, access, and refresh tokens.
- I never use an ID token as the API authorization credential.
- I can inspect `iss`, `aud`, `exp`, `scp`, and `kid` and know why they matter.
- I can explain local JWT validation vs introspection.

## Okta configuration

- I understand the important OIDC app settings.
- I can configure redirect/logout URIs deliberately.
- I can reason about assignments/Controlled Access.
- I know when Trusted Origins/CORS matters.
- I can configure or troubleshoot the client authentication method.

## Authorization

- I understand scopes, claims, groups, and audience without mixing them.
- I understand that the client requests a scope and the policy permits/denies it.
- I understand access-policy ordering.
- I separate Authorization Server Access Policy from Global Session/App Sign-In Policy.

## API

- I can protect an API with access tokens.
- I can validate signature, issuer, audience, lifetime, and signing key.
- I authorize after validation using scopes/claims appropriate to the API.
- I can reason about 401 vs 403.

## Sessions/lifecycle

- I can explain Okta session vs application session vs tokens.
- I can explain why logout can still result in immediate SSO.
- I can refresh and revoke tokens and explain the expected behavior.
- I understand when local validation will not give me current revocation state.

## Automation

- I can implement Client Credentials for M2M.
- I can implement an Okta API Service app using `private_key_jwt`.
- I understand both Okta API scopes and admin role/resource permissions.
- I can troubleshoot a bad client assertion.

## Troubleshooting

- I follow the transaction instead of changing random settings.
- I can identify whether failure is at `/authorize`, authentication policy, callback, `/token`, token validation, or API authorization.
- I use Network/Postman + token evidence + System Log to prove the cause.
- I can explain the root cause to an application owner in plain language.

If these are true, you have the working model needed for normal implementation-engineer work. The remaining gaps will usually be product-specific or edge-case features that you can learn from vendor documentation when a project actually requires them.

---

# What to skip for now

Do **not** spend your 15 days studying these deeply:

- OAuth history
- OAuth 1.0
- reading RFCs line by line
- RSA/ECDSA mathematics
- building your own authorization server
- JWE internals
- exotic protocol attack research
- every OAuth extension

## Recognize, but do not master until needed

Know what these names roughly mean so they do not surprise you in a project:

- Implicit flow — legacy; do not choose it for a modern SPA when PKCE is available
- Resource Owner Password — legacy/high-risk; do not design new normal solutions around it
- Device Authorization — useful for constrained devices
- Interaction Code — Okta Identity Engine embedded authentication
- Token Exchange
- Dynamic Client Registration
- `client_secret_jwt` — supported client authentication method; recognize it, learn details if an integration uses it
- OIN-specific OAuth/OIDC restrictions — check the current OIN requirements when publishing an integration to the Okta Integration Network
- Token Inline Hook — lets Okta call an external service during token issuance to customize token claims; learn it when a project requires dynamic/external token enrichment
- PAR
- JAR
- JARM
- DPoP — proof-of-possession style protection that binds token use to a key; learn it when a higher-security project requires it
- FAPI — specialized high-assurance/financial API profiles

If a real project requires one of these, learn it then. Your strong foundation will make it much faster.

The next section promotes five of these from "recognize only" to "working knowledge" — but only as a **second pass**, after the core course is reflex.

---

# Appendix — Advanced OAuth/OIDC (in-scope, for a later pass)

Do **not** study this during the 15 days. It is here so that once the core is second nature — you can design, build, and troubleshoot the five integrations without looking things up — you have a clear path to close the last 10% and gain working knowledge of the less-common OAuth/OIDC patterns that appear in advanced projects (still no SAML or SCIM; those are separate courses).

Everything below is OAuth/OIDC-scoped. Treat each item the same way as the core: understand it, run it, break it, explain it.

## A. DPoP — sender-constrained tokens

**What it is:** Demonstrating Proof-of-Possession. The client holds a key pair and sends a signed **DPoP proof JWT** in a `DPoP` header on each request. The access token is bound to that key (a `cnf`/`jkt` thumbprint), and its type becomes `DPoP`, not `Bearer`.

**Why it matters:** a stolen `Bearer` token is replayable by anyone. A DPoP-bound token is useless without the private key, so it is showing up in higher-security Okta integrations. Okta supports DPoP for API access.

**Day-to-day / troubleshooting angle:**

```text
token_type = DPoP, not Bearer
DPoP proof required on every call (htm = method, htu = URL, iat, jti)
use_dpop_nonce challenge -> retry proof with the returned DPoP-Nonce
clock skew or htu/htm mismatch -> proof rejected
```

**Lab:** enable DPoP on an app, capture the `DPoP` header and the bound access token, then break `htu`, `htm`, and the nonce in turn and read the `401` + `DPoP-Nonce` responses.

## B. Token Exchange (On-Behalf-Of) — delegation in service chains

**What it is:** Okta's On-Behalf-Of (OBO) Token Exchange, `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`. When API1 calls API2 on behalf of a user, API1 **authenticates as the OAuth client** and passes the user's incoming access token as `subject_token`; Okta returns a new token scoped for the downstream API.

**Why it matters:** in a chain (API1 → API2 for a user), you must not forward the original token to the wrong audience. OBO mints a correctly-scoped downstream token that still identifies the original user. Configured on an Okta authorization server.

**The request (OBO shape):**

```text
grant_type   = token-exchange
subject_token = user's incoming access token
subject_token_type = access_token
scope        = downstream (API2) scopes
audience     = downstream authorization-server audience
+ API1 authenticates itself as the OAuth client
```

**The result:**

```text
new access token
  aud = API2's configured Custom Authorization Server audience
  scp = API2 permissions
  sub = original user        (delegation is preserved)
  cid = API1 service client   (which service made the call)
```

Note: Okta's standard OBO example does **not** use an `actor_token` or an `act` claim — use the System Log to see which service acted for which user. (`act` appears in the separate AI-agent / ID-JAG delegation scenario, which is a different use case.)

**Lab:** configure the token-exchange grant, have API1 exchange an incoming user token for a token scoped to API2, then inspect `aud`, `scp`, `sub`, and `cid` before and after.

## C. Consent

**What it is:** a scope can require user or admin **consent**. The user sees a consent prompt; consent can later be granted or revoked; `prompt=consent` forces the screen.

**Why it matters:** an unexpected consent screen — or an API call blocked until consent — is a real ticket, and it is a **different layer** from MFA and from an access-policy denial.

**Day-to-day / troubleshooting angle:** distinguish "blocked by missing consent" from "denied by authorization-server policy" from "authentication/MFA prompt." Each has a different fix and a different System Log signature.

**Lab:** mark a custom scope as requiring consent, trigger the prompt, grant it, then revoke the grant and observe how the next authorization behaves.

## D. Inbound federation and external IdP (OIDC side)

**What it is:** Okta consuming an **external Identity Provider**. Add an external **OIDC** IdP in Okta, route users to it with **IdP routing rules**, and, when required, configure **JIT provisioning/account linking** for federated users.

**Why it matters:** in real organizations, the user often authenticates somewhere else and arrives through Okta. Login problems then have an extra hop: "who actually authenticated this user, and what did Okta receive?" The routing, attribute mapping, and JIT logic are OAuth/OIDC-adjacent and cause real failures.

**Scope note:** an external IdP can also be a **SAML** IdP. The routing/JIT/attribute-mapping concepts are the same, but SAML specifics belong to the SAML course. Here, learn it with an **OIDC** external IdP.

**Day-to-day / troubleshooting angle:**

```text
user -> Okta routing rule -> external OIDC IdP -> back to Okta -> your app
break points: routing rule match, IdP client config, attribute/claim mapping, JIT rules
```

**Lab:** add an external OIDC IdP, create a routing rule, trace a full login through the IdP and back, then break the routing rule and an attribute mapping and diagnose each from the System Log.

## E. Deeper security — attack to defense

The core course teaches the practical security *rules*. On the second pass, connect each defense you already use to the attack it stops, so the design choices stop feeling arbitrary.

| Attack | Defense you already use |
|---|---|
| Authorization-code interception | PKCE (`S256`) |
| Request forgery on the browser flow | `state` |
| ID-token replay | `nonce` |
| Open-redirect abuse | exact registered redirect URIs |
| Token leakage | HTTPS, no tokens in URLs, no token logging |
| Authorization-server mix-up | validate `iss`; distinct redirect URIs per AS |
| Refresh-token exposure/theft | **prevent:** secure storage and minimize exposure. **detect/limit replay:** rotation + reuse detection. **limit impact:** appropriate lifetime |
| Forged/altered token accepted | validate signature, `iss`, `aud`, `exp` — not just "it decodes" |
| Token theft from a SPA (XSS) | **prevent:** XSS/CSP hardening + keep tokens out of browser JS (BFF / HttpOnly cookies). **limit impact only:** short lifetimes + refresh rotation |
| Replay of a stolen bearer token | DPoP (Appendix A) |

**Lab:** for each row, remove or weaken the defense in your lab environment and demonstrate the failure it is meant to prevent. That is the difference between reciting security rules and understanding them.

## How to know you have finished the second pass

You can explain, on a whiteboard, when you would reach for DPoP, Token Exchange, or an external IdP; you can tell a consent denial from a policy denial from an MFA prompt by its System Log signature; and for every parameter in the core flow you can name the attack it defends against. At that point you have working knowledge of the less-common OAuth/OIDC patterns on top of a solid core — the remaining unknowns are product-version details you look up when a project needs them. No engineer is "complete" on every OAuth/OIDC vendor variation, and you do not need to be.

---

# Official Okta references worth bookmarking

Use these as engineering references rather than material to memorize:

- OAuth 2.0 and OpenID Connect overview: https://developer.okta.com/docs/concepts/oauth-openid/
- Authorization servers: https://developer.okta.com/docs/concepts/auth-servers/
- Authorization Code with PKCE: https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/
- Client authentication methods: https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth
- Validate access tokens: https://developer.okta.com/docs/guides/validate-access-tokens/main/
- Refresh tokens: https://developer.okta.com/docs/guides/refresh-tokens/main/
- Configure authorization-server access policies: https://developer.okta.com/docs/guides/configure-access-policy/main/
- Global Session and App Sign-In policies: https://developer.okta.com/docs/guides/configure-signon-policy/main/
- OAuth for Okta API service apps: https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/
- Revoke tokens: https://developer.okta.com/docs/guides/revoke-tokens/main/
- Redirect vs embedded authentication: https://developer.okta.com/docs/concepts/redirect-vs-embedded/

For the advanced appendix (second pass only):

- DPoP: https://developer.okta.com/docs/guides/dpop/
- On-Behalf-Of Token Exchange: https://developer.okta.com/docs/guides/set-up-token-exchange/main/
- External identity providers + IdP Discovery/routing: https://developer.okta.com/docs/concepts/identity-providers/
- Add an external OIDC Identity Provider: https://developer.okta.com/docs/guides/add-an-external-idp/openidconnect/main/
- Custom consent / scopes: https://developer.okta.com/docs/guides/request-user-consent/main/

The point of bookmarking these is not to read every page before you start. Use them when a lab or project gives you a reason to look something up. Okta doc URLs and feature availability change over time, so confirm the current page and whether a feature is enabled in your tenant before relying on it.