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
