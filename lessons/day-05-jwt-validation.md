# Day 5 - JWT Validation, Discovery, and JWKS

## Goal for today

Day 4 showed that an ID token can be decoded and read.

Today you learn when an ID token can actually be trusted.

By the end of Day 5, you should understand:

- JWT header, payload, and signature
- why decoding proves almost nothing about trust
- what an expected issuer is
- what OIDC discovery is
- what a JWKS is
- what kid means
- how a validator chooses a public signing key
- what signature validation proves
- why alg must be restricted to the expected algorithm
- how issuer, audience, expiration, and nonce are validated
- why the application starts from a configured trusted issuer
- how signing-key rotation affects validation
- what to do when kid is unknown
- the difference between token validation and authorization

This lesson validates the ID token from the same org authorization server used in Days 3 and 4.

We still do not use the org authorization server access token as a custom API token.

[Open the Day 5 flow diagrams](../diagrams/day-05-jwt-validation.md)

## Start with a dangerous assumption

Suppose someone sends you a JWT.

You decode it and see:

~~~json
{
  "iss": "https://your-org.okta.com",
  "aud": "your-client-id",
  "email": "employee@example.com",
  "exp": 1780000000
}
~~~

Everything looks reasonable.

Can you trust it?

No.

Anyone can create JSON and Base64URL-encode it.

Readable claims are not proof.

The real question is:

> Can I prove that this token was signed by the trusted issuer, was intended for my client, is still valid, and belongs to the transaction I expect?

That is validation.

## JWT structure

A JWT has three sections:

~~~text
header.payload.signature
~~~

Example:

~~~text
xxxxx.yyyyy.zzzzz
  |     |     |
  |     |     +-- signature
  |     +-------- payload
  +-------------- header
~~~

## Header

A typical Okta ID token header looks conceptually like:

~~~json
{
  "alg": "RS256",
  "kid": "abc123"
}
~~~

### alg

alg identifies the signing algorithm.

For the Okta ID tokens we validate in this course:

~~~text
alg = RS256
~~~

The validator should restrict accepted algorithms to what the application expects.

Do not let an untrusted token freely choose any algorithm the library supports.

### kid

kid means key ID.

Okta can publish multiple public keys.

The kid tells the validator which public key corresponds to the private key used to sign the token.

~~~text
JWT header
kid = abc123
     |
     v
JWKS
     |
     +-- key kid=111
     +-- key kid=abc123  <-- matching key
     +-- key kid=999
~~~

## Payload

The payload contains claims.

For an ID token, important claims include:

~~~text
iss
sub
aud
iat
exp
nonce, when requested
~~~

The payload is readable before validation.

Do not trust it until validation succeeds.

## Signature

The signature lets the validator detect tampering and verify that the token was signed using a private key corresponding to a trusted published public key.

You do not need the RSA mathematics for implementation work.

You need the trust relationship:

~~~text
Okta holds signing private key
        |
        | signs token
        v
JWT signature

Okta publishes corresponding public key
        |
        v
Client verifies signature
~~~

The public key verifies signatures.

It cannot be used to create a valid Okta signature.

## Where does the public key come from?

Do not copy a public key into the application and assume it never changes.

The client starts from an issuer it already trusts.

For our org authorization server:

~~~text
Expected issuer:
https://YOUR-OKTA-DOMAIN
~~~

From that configured issuer, the application retrieves the OIDC discovery document.

For the org authorization server:

~~~text
https://YOUR-OKTA-DOMAIN/.well-known/openid-configuration
~~~

The discovery document contains metadata such as:

~~~text
issuer
authorization_endpoint
token_endpoint
jwks_uri
userinfo_endpoint
supported algorithms
~~~

The important field for today's validation is:

~~~text
jwks_uri
~~~

## Discovery trust direction

Correct:

~~~text
Application configuration contains expected trusted issuer
        |
        v
Retrieve that issuer's discovery document
        |
        v
Read jwks_uri from trusted metadata
        |
        v
Retrieve signing keys
~~~

Dangerous:

~~~text
Receive untrusted token
        |
        v
Read arbitrary iss from token
        |
        v
Blindly trust whatever server that value points to
~~~

The expected issuer comes from application configuration.

The token must match that expected issuer.

Do not let the token decide which issuer you trust.

## What is JWKS?

JWKS means JSON Web Key Set.

It is a document containing public keys.

Conceptual example:

~~~json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "abc123",
      "use": "sig",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
~~~

You do not manually perform RSA operations with n and e in normal application code.

A maintained JWT library handles that work.

Your responsibility is understanding where the key came from and why it is trusted.

## The kid lookup

Validation reads the token header.

Example:

~~~text
kid = abc123
~~~

The validator looks for:

~~~text
JWKS key where kid == abc123
~~~

If found:

~~~text
matching public key
        |
        v
verify token signature
~~~

If no matching key exists, the token cannot currently be verified with the available key set.

## Why unknown kid does not immediately mean attack

Signing keys rotate.

A validator may have cached an older JWKS.

A sensible flow is:

~~~text
kid not found in cached JWKS
        |
        v
refresh JWKS from trusted jwks_uri
        |
        v
look again
        |
        +-- found --> continue validation
        |
        +-- still missing --> reject token
~~~

Do not hardcode one public key forever.

Okta publishes signing keys dynamically and rotates keys.

Libraries should cache and refresh keys appropriately.

## What signature validation proves

If signature verification succeeds with a public key obtained from the trusted issuer's JWKS, it proves that the signed token content has not been modified since signing and that the signature corresponds to that signing key.

But signature validation alone is not enough.

A correctly signed token might still be:

~~~text
for another client
from another authorization server
expired
unrelated to the authentication transaction
~~~

Claims must also be validated.

## ID token validation checks

At a practical level, validate:

~~~text
1. Expected signing algorithm
2. Signature using trusted current public key
3. iss
4. aud
5. exp
6. iat as appropriate
7. nonce when one was used
8. other required OIDC checks
~~~

A maintained OIDC/JWT library should perform most of this.

Do not hand-write cryptographic verification in production.

## Validate iss

iss means issuer.

For our current org authorization server:

~~~text
expected iss =
https://YOUR-OKTA-DOMAIN
~~~

Validation asks:

> Does the token's issuer exactly match the authorization server this client trusts?

If not, reject it.

A token from another Okta org is not trusted just because it is also an Okta token.

## Validate aud

aud means audience.

For an ID token:

~~~text
expected aud =
your OIDC client ID
~~~

Validation asks:

> Was this ID token issued for my client?

A validly signed token issued for another application should not be accepted by your client.

## Validate exp

exp means expiration time.

Validation asks:

> Is the current time before the token's expiration?

If the token is expired, reject it.

Applications normally allow a small configured clock skew.

Do not use large leeway just to make expiration errors disappear.

Fix incorrect system time.

## Validate iat

iat means issued-at time.

It tells you when the token was issued.

The local system clock matters for time-based validation.

## Validate nonce

In our Day 3 and Day 4 flows, the client sent a nonce.

The ID token should contain the corresponding nonce.

~~~text
expected nonce from authorization transaction
                |
                | compare
                v
nonce in validated ID token
~~~

If they do not match, reject the authentication response.

Important:

> Verify the token signature and core claims before trusting the nonce claim you decoded.

## Practical validation pipeline

The internal order used by libraries can vary, but your reasoning should cover this trust chain:

~~~text
Expected issuer configured by application
        |
        v
Fetch trusted discovery metadata
        |
        v
Obtain jwks_uri
        |
        v
Read token header
        |
        v
Check expected algorithm
        |
        v
Find public key by kid
        |
        v
Verify signature
        |
        v
Validate iss
        |
        v
Validate aud
        |
        v
Validate time claims
        |
        v
Validate nonce when used
        |
        v
ID token can be trusted for its intended OIDC purpose
~~~

Do not stop halfway.

## Validation and authorization are different

Suppose the ID token validates successfully.

That tells the client it has a trusted authentication token for the expected client and transaction.

It does not automatically answer:

> Can this user approve payroll?

That is an application authorization decision.

For a future API:

~~~text
First:
Can I trust the access token?

Then:
Does the trusted token grant the permission required by this endpoint?
~~~

Those are separate decisions.

## Org authorization server access-token warning

Day 5 validates the ID token from the org authorization server.

Do not turn today's exercise into local validation of the org authorization server access token.

Okta states that org authorization server access tokens are intended for Okta and should be considered opaque by your applications.

~~~text
Day 5:
validate ID token for the client

Later:
validate Custom Authorization Server access token for our API
~~~

## Local validation

JWT validation can happen locally after the validator has the required trusted public key.

~~~text
Client
  |
  | token
  v
validation library
  |
  +-- cached discovery / JWKS
  +-- signature checks
  +-- claim checks
  |
  v
valid or invalid
~~~

The application does not need a network call to Okta for every local validation after appropriate metadata and key caching.

## Key rotation and caching

Public signing keys can rotate.

A production validator should:

~~~text
retrieve keys dynamically
cache them appropriately
honor cache behavior
refresh when needed
handle unknown kid
reject when no trusted key can verify the token
~~~

Do not hardcode one public signing key forever.

## Common mistakes

### Mistake 1: It decodes, so it is valid

Wrong.

Anyone can encode a JWT-looking payload.

### Mistake 2: Signature valid, so accept it

Incomplete.

Issuer, audience, expiration, nonce, and other required checks still matter.

### Mistake 3: Trust the issuer named by the token automatically

Wrong.

The application begins with an expected trusted issuer.

### Mistake 4: Hardcode one signing public key forever

Wrong.

Signing keys rotate.

### Mistake 5: Ignore aud

Wrong.

A token for another client should not be accepted as your ID token.

### Mistake 6: Ignore exp

Wrong.

A correctly signed expired token is still expired.

### Mistake 7: Ignore nonce after sending one

Wrong.

If the request used nonce, validate it.

### Mistake 8: Validate the org authorization server access token for your custom API

Wrong.

That token is not intended for your custom resource server.

## What you should be able to explain

1. What are the three JWT sections?
2. What does kid identify?
3. What does alg tell the validator?
4. What is OIDC discovery?
5. What is jwks_uri?
6. What is JWKS?
7. Why does the validator start from a configured issuer?
8. What does signature verification prove?
9. Why is signature verification alone insufficient?
10. What should aud equal for our ID token?
11. What should iss equal?
12. Why does exp matter?
13. When should nonce be checked?
14. Why do signing keys rotate?
15. What should happen when kid is unknown?
16. Why is token validation separate from authorization?

## Day 5 lab

[Day 5 Lab - Validate a Real Okta ID Token](../labs/day-05-jwt-validation.md)

## Day 5 completion standard

Day 5 is complete when you can explain:

~~~text
configured issuer
        |
        v
discovery
        |
        v
jwks_uri
        |
        v
kid selects public key
        |
        v
signature validation
        |
        v
issuer + audience + time + nonce checks
        |
        v
trusted ID token
~~~

## Official references

- [Okta: Validate ID tokens](https://developer.okta.com/docs/guides/validate-id-tokens/main/)
- [Okta: Key rotation](https://developer.okta.com/docs/concepts/key-rotation/)
- [Okta: OpenID Connect and OAuth 2.0](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/overview)
