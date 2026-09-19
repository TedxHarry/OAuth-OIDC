# Day 5 Flow Diagrams

These diagrams support the Day 5 lesson.

## 1. JWT structure

**Question answered:** What are the three sections of a JWT?

~~~mermaid
flowchart LR
    H["HEADER<br/><br/>alg<br/>kid"]
    P["PAYLOAD<br/><br/>iss<br/>sub<br/>aud<br/>iat<br/>exp<br/>nonce"]
    S["SIGNATURE<br/><br/>cryptographic signature"]

    H --> DOT1["."]
    DOT1 --> P
    P --> DOT2["."]
    DOT2 --> S
~~~

Readable header and payload do not prove the signature is valid.

## 2. Trust starts from the configured issuer

**Question answered:** Where should discovery and signing keys come from?

~~~mermaid
flowchart TB
    CFG["APPLICATION CONFIGURATION<br/>Expected trusted issuer<br/>https://your-org.okta.com"]
    DISC["OIDC DISCOVERY<br/>/.well-known/openid-configuration"]
    META["TRUSTED METADATA<br/>issuer<br/>authorization_endpoint<br/>token_endpoint<br/>jwks_uri"]
    JWKS["JWKS<br/>Published public signing keys"]

    CFG --> DISC --> META --> JWKS
~~~

Do not let an untrusted token choose an issuer that the application automatically trusts.

## 3. kid selects the signing key

**Question answered:** How does the validator know which public key to use?

~~~mermaid
flowchart LR
    TOKEN["ID TOKEN HEADER<br/>kid = key-B"]
    SET["JWKS<br/><br/>key-A<br/>key-B<br/>key-C"]
    MATCH["MATCH<br/>public key-B"]
    VERIFY["Use key-B<br/>to verify signature"]

    TOKEN --> SET --> MATCH --> VERIFY
~~~

## 4. Complete ID-token validation pipeline

**Question answered:** What must be checked before the token is trusted?

~~~mermaid
flowchart TB
    START["1. Receive ID token"]
    ISSUER["2. Use configured<br/>expected issuer"]
    DISC["3. Retrieve or use cached<br/>discovery and JWKS"]
    ALG{"4. alg is expected<br/>RS256?"}
    KID{"5. Matching kid<br/>available?"}
    REFRESH["Refresh JWKS from<br/>trusted jwks_uri"]
    KID2{"Matching kid<br/>available now?"}
    SIG{"6. Signature valid?"}
    ISS{"7. iss equals<br/>expected issuer?"}
    AUD{"8. aud includes<br/>this client ID?"}
    TIME{"9. Time claims valid?<br/>exp not expired"}
    NONCE{"10. Nonce was used?"}
    NMATCH{"11. nonce equals<br/>expected nonce?"}
    VALID["VALID ID TOKEN<br/>for intended OIDC use"]
    REJECT["REJECT"]

    START --> ISSUER --> DISC --> ALG
    ALG -->|No| REJECT
    ALG -->|Yes| KID
    KID -->|Yes| SIG
    KID -->|No| REFRESH --> KID2
    KID2 -->|No| REJECT
    KID2 -->|Yes| SIG
    SIG -->|No| REJECT
    SIG -->|Yes| ISS
    ISS -->|No| REJECT
    ISS -->|Yes| AUD
    AUD -->|No| REJECT
    AUD -->|Yes| TIME
    TIME -->|No| REJECT
    TIME -->|Yes| NONCE
    NONCE -->|No| VALID
    NONCE -->|Yes| NMATCH
    NMATCH -->|No| REJECT
    NMATCH -->|Yes| VALID
~~~

The exact internal order can differ by library. The required trust checks still need to happen.

## 5. Decoding vs validation

**Question answered:** Why is a token decoder not a security validator?

~~~mermaid
flowchart LR
    JWT["JWT string"]
    DEC["Base64URL decode"]
    CLAIMS["Readable JSON claims"]
    Q{"Signature + issuer + audience<br/>time + nonce validated?"}
    NO["NO<br/>Readable only<br/>NOT TRUSTED"]
    YES["YES<br/>Trusted for intended use"]

    JWT --> DEC --> CLAIMS --> Q
    Q -->|No| NO
    Q -->|Yes| YES
~~~

## 6. Unknown kid and key rotation

**Question answered:** What should happen if the cached JWKS does not contain the token kid?

~~~mermaid
flowchart TB
    TOKEN["Token header<br/>kid = new-key"]
    CACHE["Cached JWKS"]
    FOUND{"kid found?"}
    REFRESH["Refresh JWKS from<br/>trusted jwks_uri"]
    FOUND2{"kid found now?"}
    CONTINUE["Continue signature validation"]
    REJECT["Reject token"]

    TOKEN --> CACHE --> FOUND
    FOUND -->|Yes| CONTINUE
    FOUND -->|No| REFRESH --> FOUND2
    FOUND2 -->|Yes| CONTINUE
    FOUND2 -->|No| REJECT
~~~

Unknown kid can be caused by key rotation, stale cache, wrong issuer, or an invalid token.

Do not bypass validation.

## 7. Validation vs authorization

**Question answered:** What happens after a token becomes trusted?

This diagram is a **future API access-token example**. Our Day 5 hands-on lab is validating an ID token for the client.

~~~mermaid
flowchart TB
    TOKEN["Incoming token"]
    VALIDATE["TOKEN VALIDATION<br/>signature<br/>issuer<br/>audience<br/>time"]
    TRUST{"Trusted?"}
    AUTHZ["AUTHORIZATION<br/>scope<br/>claim<br/>role<br/>application rule"]
    ALLOW["Allow operation"]
    DENY["Deny operation"]
    REJECT["Reject credential"]

    TOKEN --> VALIDATE --> TRUST
    TRUST -->|No| REJECT
    TRUST -->|Yes| AUTHZ
    AUTHZ -->|Allowed| ALLOW
    AUTHZ -->|Not allowed| DENY
~~~

A valid token does not automatically authorize every operation.
