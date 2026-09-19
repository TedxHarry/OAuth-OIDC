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
