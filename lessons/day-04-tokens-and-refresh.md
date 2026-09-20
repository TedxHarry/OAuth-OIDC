# Day 4 - ID Tokens, Access Tokens, and Refresh Tokens

## Goal for today

Day 3 ended with Okta returning tokens.

Today we stop and understand what each token is for.

By the end of Day 4, you should understand:

- why there are different token types
- who consumes an ID token
- who consumes an access token
- who consumes a refresh token
- why an ID token is not an API bearer credential
- why a refresh token is not sent to an API
- what token expiration means
- why access tokens are usually short-lived
- what offline_access does
- how a refresh token obtains new tokens
- why refresh tokens are sensitive
- what refresh token rotation means at a practical level
- why decoding a JWT is not the same as validating it
- why the org authorization server access token from our current lab must not be used as a custom API token

This lesson builds directly on Day 3.

[Open the Day 4 flow diagrams](../diagrams/day-04-token-lifecycle.md)

## Start with the Day 3 response

At the end of Day 3, the token endpoint returned a response similar to:

~~~json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "access_token": "...",
  "scope": "openid profile email",
  "id_token": "..."
}
~~~

When refresh-token capability is enabled and requested, the response can also contain:

~~~json
{
  "refresh_token": "..."
}
~~~

A common beginner mistake is to see three long strings and think:

> They are all OAuth tokens, so they are basically interchangeable.

They are not.

Each one has a different job and a different consumer.

## Start with the consumer

Use this rule:

~~~text
ID token
   |
   v
Client application


Access token
   |
   v
Resource server


Refresh token
   |
   v
Authorization server /token endpoint
~~~

Ask:

> Who is the token intended for, and which component should consume or present it?

There is an important delivery distinction:

```text
At token issuance:
Okta returns ID, access, and refresh tokens to the client.

After issuance:
ID token
-> client validates and consumes it

Access token
-> client presents it to the intended resource server

Refresh token
-> client stores it and later presents it back to the authorization server /token endpoint
```

So "consumer" does not mean Okta sends each token directly to that component.

That distinction eliminates many design mistakes.

## ID token

The ID token is part of OpenID Connect.

Its purpose is to give the client application verifiable information about the authentication event and authenticated user.

In our Day 3 flow:

~~~text
Employee authenticates with Okta
        |
        v
Okta issues ID token
        |
        v
SPA client receives ID token
        |
        v
Client validates it
        |
        v
Client can establish authenticated application state
~~~

The ID token is intended for the client.

## ID token format

An ID token is a JSON Web Token, or JWT.

A JWT normally looks like:

~~~text
xxxxx.yyyyy.zzzzz
~~~

There are three dot-separated sections:

~~~text
header.payload.signature
~~~

At a high level:

~~~text
HEADER
-> information about the token and signing algorithm

PAYLOAD
-> claims

SIGNATURE
-> cryptographic signature used during validation
~~~

Day 5 teaches JWT validation in detail.

Today we only inspect the structure and a few claims.

## ID token claims

An ID token contains base claims and can contain additional claims depending on the flow, requested scopes, and configuration.

Do not assume that requesting `profile` or `email` guarantees every corresponding user claim will appear in the ID token. With an access token present, `/userinfo` is also an OIDC source for scope-dependent user claims.

An ID token can contain claims such as:

~~~json
{
  "iss": "https://example.okta.com",
  "sub": "00u...",
  "aud": "0oa...",
  "exp": 1780000000,
  "iat": 1779996400,
  "nonce": "...",
  "email": "user@example.com"
}
~~~

Do not memorize the JSON.

Understand the questions each claim helps answer.

### iss

iss means issuer.

Question:

> Who issued this token?

### sub

sub means subject.

Question:

> Which subject or user does this token refer to?

### aud

aud means audience.

For an ID token, the audience identifies the client the token is intended for.

In our lab, the client ID should be represented in the ID token audience.

### exp

exp means expiration time.

Question:

> After what time must this token no longer be accepted?

### iat

iat means issued-at time.

Question:

> When was this token issued?

### nonce

If the authorization request included a nonce, the ID token can contain that nonce.

The client compares it with the nonce associated with the authentication request.

This connects directly to Day 3.

## Decoding is not validation

This distinction is critical.

A JWT payload is encoded, not encrypted.

You can decode it and read the claims.

That does not prove:

~~~text
who issued it
whether the signature is valid
whether the issuer is trusted
whether the audience is correct
whether it is expired
whether the nonce is correct
~~~

So:

~~~text
Decode JWT
     !=
Validate JWT
~~~

Day 4:

~~~text
inspect and understand
~~~

Day 5:

~~~text
verify trust and validity
~~~

## Access token

The access token has a different job.

It represents authorization to access a protected resource.

A client presents it to a resource server.

Generic example:

~~~http
GET /api/profile
Authorization: Bearer <access_token>
~~~

The resource server decides whether the access token is acceptable for that resource and operation.

The ID token should not replace the access token.

## Why the ID token is not the API token

Suppose the client sends an ID token to a custom API:

~~~http
Authorization: Bearer <id_token>
~~~

That is the wrong token type.

The ID token is intended for the client application.

The API should receive an access token intended for that API.

The fact that an ID token is signed and contains claims does not turn it into an API access credential.

## Important Day 4 boundary: our org authorization server access token

In Day 3 and Day 4, we use the Okta org authorization server:

~~~text
https://{yourOktaDomain}
~~~

Its endpoints include:

~~~text
/oauth2/v1/authorize
/oauth2/v1/token
~~~

Okta states that access tokens issued by the org authorization server are intended for Okta to consume and verify.

They are not intended to be validated or used by your own custom resource server.

Therefore, for the access token from our current lab:

~~~text
Do:
-> treat it as an opaque credential
-> use it only where the authorization server intended

Do not:
-> build your custom API around its internal claims
-> assume its internal structure is a stable contract
~~~

Later, when we protect our own Employee API, we will use a Custom Authorization Server and an access token intended for our API.

## Access token format is not the main contract

An access token may look like a JWT.

That does not mean the client should depend on its internal claims.

The client normally uses the access token.

The resource server validates it according to the authorization-server design.

For the Okta org authorization server specifically, Okta says the token contents can change without notice.

So in this course:

~~~text
ID token
-> inspect claims as part of OIDC learning

Org-AS access token
-> do not build custom application logic from its contents
~~~

## Refresh token

A refresh token solves a lifecycle problem.

Access tokens should not need to remain valid for a very long time just to avoid making the user sign in repeatedly.

Instead:

~~~text
Shorter-lived access token
        |
        | expires
        v
Client uses refresh token
        |
        v
Authorization server /token
        |
        v
New access token
~~~

The refresh token is a credential used with the authorization server.

The client should treat the refresh token as an opaque credential. Do not build application logic by decoding or depending on its internal format.

It is not sent to the resource server.

## Who consumes the refresh token?

The refresh token goes back to:

~~~text
Authorization server
        |
        v
/token
~~~

It does not go to a custom resource server.

Its purpose is to obtain new tokens.

## Why refresh tokens are sensitive

A refresh token can often be used for longer than an access token.

It can obtain additional access tokens without requiring the user to sign in again.

That makes it highly sensitive.

~~~text
Access token compromised
-> attacker may have access until token expires or is revoked

Refresh token compromised
-> attacker may be able to request more access tokens
~~~

This is why storage, rotation, lifetime, and reuse detection matter.

## What is offline_access?

In an Authorization Code flow, if the client needs a refresh token, it requests the OIDC scope:

~~~text
offline_access
~~~

For this flow, Okta requires offline_access to be requested as part of the authorization request to /authorize.

Example:

~~~text
scope=openid profile email offline_access
~~~

It is not enough to add offline_access only to the authorization-code /token request.

The app integration must also allow the Refresh Token grant type.

Think of both conditions:

~~~text
App configuration allows Refresh Token
                    +
Authorization request asks for offline_access
                    |
                    v
Refresh token can be issued
~~~

Other authorization conditions can still apply.

## Refresh token request

After the client has a refresh token, it can call the token endpoint again.

For our public SPA client, the request shape is:

~~~http
POST /oauth2/v1/token
Content-Type: application/x-www-form-urlencoded
Accept: application/json
~~~

Body:

~~~text
grant_type=refresh_token
client_id={clientId}
redirect_uri=http://localhost:8000/callback
scope=openid profile email offline_access
refresh_token={refreshToken}
~~~

There is no client secret for our SPA.

If the refresh request is valid, new tokens are returned.

## Why include openid during refresh?

If the client wants an ID token as part of the refreshed response, include:

~~~text
openid
~~~

The scopes requested during refresh must stay within what was originally granted.

## Refresh token rotation

A long-lived refresh token is powerful, especially in a public client.

A browser-based application cannot guarantee that a persistent credential stored in the browser is accessible only to the intended application code. A browser compromise such as script injection can expose stored credentials.

Rotation reduces the risk of repeatedly using one persistent refresh token. It does not make unsafe browser code safe, but it limits and detects replay behavior when used with Okta's reuse-detection controls.

At a high level:

~~~text
Client has refresh token R1
        |
        v
R1 sent to /token
        |
        v
New access token returned
        |
        v
A replacement refresh token may also be returned
        |
        v
Client must follow the currently valid refresh-token state
~~~

For SPA integrations, Okta uses rotating refresh token behavior by default when Refresh Token is enabled.

The exact response and reuse behavior depends on the app's rotation, lifetime, and grace-period settings.

Practical rule:

> If Okta returns a new refresh token, the client must securely replace its stored refresh token with the returned one.

Do not assume the refresh token string always stays the same.

## Grace period

Rotation can create a practical problem.

~~~text
Client sends refresh token
        |
        v
Okta rotates it
        |
        v
Network response is lost
~~~

The client might not receive the replacement token.

A grace period can allow the previous refresh token to remain usable briefly.

This helps with network and concurrency problems.

Detailed reuse detection belongs later in the course.

For Day 4, understand why the grace period exists.

## Token expiration

Tokens are not intended to be accepted forever.

A token response often contains:

~~~json
{
  "expires_in": 3600
}
~~~

That tells the client how many seconds the access token is valid from issuance.

For the Okta Org Authorization Server used in our current lab, Okta currently documents a 60-minute access-token lifetime and a 60-minute ID-token lifetime. Later, with a Custom Authorization Server, access-token lifetime can be configured by policy.

An ID token also contains an exp claim.

Expiration creates a boundary:

~~~text
token issued
    |
    v
valid period
    |
    v
expiration
    |
    v
token must no longer be accepted
~~~

Do not design applications that ignore expiration.

## Why not make the access token valid for a week?

Long access-token lifetimes increase the damage window if the token is exposed.

A common safer lifecycle is:

~~~text
shorter-lived access token
        |
        v
refresh mechanism when continued access is appropriate
~~~

Token lifetimes are an engineering and security decision.

The lesson is not "always make every token as short as possible."

The lesson is:

> Do not make access tokens extremely long-lived just to avoid implementing the proper renewal lifecycle.

## Token lifecycle

~~~text
Authorization
     |
     v
Token issuance
     |
     v
Token use
     |
     v
Expiration
     |
     +------------------+
     |                  |
     | refresh allowed? |
     |                  |
     +-- yes --> refresh token --> new tokens
     |
     +-- no --> new authorization/sign-in as required
~~~

Later we add:

~~~text
revocation
introspection
session logout
reuse detection
~~~

Do not mix all of those into Day 4.

## Client Credentials is different

A machine-to-machine Client Credentials service has no user authorization session to extend.

A service normally does this:

~~~text
service authenticates to token endpoint
        |
        v
access token issued
        |
        v
service uses token
        |
        v
token expires
        |
        v
service requests a new access token
~~~

Do not force the user refresh-token pattern onto Client Credentials.

Day 11 teaches that flow.

## Keep issuance path and usage path separate

A successful token response may return several tokens to the same client:

```text
Okta /token
     |
     v
Client receives:
- ID token
- access token
- refresh token
```

What happens next depends on token type:

```text
ID token
-> stays with client for OIDC authentication processing

Access token
-> client sends it to the intended resource server

Refresh token
-> client keeps it and sends it back only when requesting new tokens
```

For our current Org Authorization Server lab, the intended resource server for the access token is Okta.

Our own Employee API comes later with a Custom Authorization Server.

## Common mistakes to catch early

### Mistake 1: Sending the ID token to the API

Wrong.

The ID token is for the OIDC client.

### Mistake 2: Sending the refresh token to the API

Wrong.

The refresh token is for the authorization server token endpoint.

### Mistake 3: Assuming every long token string has the same purpose

Wrong.

Identify the token type and consumer.

### Mistake 4: Decoding a JWT and calling it validated

Wrong.

Reading claims does not prove the signature or claims are trustworthy.

### Mistake 5: Reading org authorization server access-token claims as your application contract

Wrong.

Okta says those tokens are for Okta and their contents can change.

### Mistake 6: Enabling Refresh Token but forgetting offline_access

For Authorization Code flow, the authorization request needs offline_access to request refresh-token capability.

### Mistake 7: Sending offline_access only at the authorization-code token exchange

Wrong.

Okta requires it in the authorization request for Authorization Code flow.

### Mistake 8: Assuming a refresh token is harmless because it is not sent to the API

Wrong.

A refresh token can obtain additional tokens and must be protected.

## What you should be able to explain now

1. Who consumes an ID token?
2. Who consumes an access token?
3. Who consumes a refresh token?
4. Why is the ID token not the normal API bearer token?
5. What does aud mean in the ID token at a high level?
6. What does exp mean?
7. Why is decoding different from validation?
8. Why must we treat our org authorization server access token as opaque for our custom application?
9. What problem does the refresh token solve?
10. Why is the refresh token sensitive?
11. What does offline_access do?
12. Where must offline_access be requested for Authorization Code flow?
13. What does refresh-token rotation try to improve?
14. Why can a machine-to-machine flow work without refresh tokens?

## Day 4 lab

[Day 4 Lab - Inspect Tokens and Refresh Them](../labs/day-04-token-lifecycle.md)

## Day 4 completion standard

Day 4 is complete when you can look at a token response and immediately identify:

~~~text
Which token is for the client
Which token is for a resource server
Which token returns to the authorization server
Which token should never be sent to the API
Which token should not be used as proof of user identity at an API
When refresh is appropriate
What offline_access changes
Why decoding alone proves nothing about trust
~~~

## Official references

- [Okta: Token lifecycle](https://developer.okta.com/docs/concepts/token-lifecycles/)
- [Okta: Refresh access tokens and rotate refresh tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: Validate access tokens](https://developer.okta.com/docs/guides/validate-access-tokens/main/)
