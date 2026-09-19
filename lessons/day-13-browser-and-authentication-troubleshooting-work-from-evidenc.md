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
