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
