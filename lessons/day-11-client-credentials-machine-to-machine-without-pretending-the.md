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
