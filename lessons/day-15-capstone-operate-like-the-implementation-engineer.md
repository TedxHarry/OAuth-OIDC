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
