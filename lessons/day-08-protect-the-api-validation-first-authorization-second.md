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
