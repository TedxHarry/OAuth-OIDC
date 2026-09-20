# Day 8 Flow Diagrams

These diagrams support the Day 8 lesson.

Each diagram answers one specific resource-server question.

## 1. Why the authorization server changes on Day 8

**Question answered:** Why can the Employee API not use the Org Authorization Server access token from earlier days?

~~~mermaid
flowchart LR
    ORG["Org Authorization Server<br/>Issuer: https://your-org.okta.com"]
    ORGTOKEN["Access token<br/>intended for Okta"]
    OKTA["Okta APIs"]

    CAS["Custom Authorization Server<br/>Issuer: https://your-org.okta.com/oauth2/default"]
    APITOKEN["Access token<br/>intended for your API audience"]
    API["Employee API<br/>Resource Server"]

    ORG --> ORGTOKEN --> OKTA
    CAS --> APITOKEN --> API
~~~

Working rule:

~~~text
Org Authorization Server access token
-> Okta

Custom Authorization Server access token
-> your resource server
~~~

## 2. Full Day 8 API transaction

**Question answered:** Who requests the token, who issues it, and who enforces it?

~~~mermaid
sequenceDiagram
    autonumber
    actor U as Employee
    participant C as SPA Client
    participant A as Custom Authorization Server
    participant API as Employee API

    C->>A: Authorization request<br/>scope includes employee.read
    A->>U: Authenticate user when required
    U->>A: Complete authentication

    A-->>C: Authorization code
    C->>A: Token request<br/>code + PKCE verifier
    A-->>C: Access token<br/>aud + cid + scp + exp

    C->>API: GET /api/employees<br/>Authorization: Bearer access_token

    Note over API: STEP 1<br/>Validate token trust

    Note over API: STEP 2<br/>Check employee.read in scp

    API-->>C: 200, 401, or 403
~~~

The API does not trust the browser login event. It evaluates the bearer token presented to the API.

## 3. Validate first, authorize second

**Question answered:** What is the API decision sequence?

~~~mermaid
flowchart TB
    REQ["GET /api/employees"]
    PRESENT{"Bearer token present?"}
    HEADER{"JWT header acceptable?"}
    KEY{"Trusted signing key found?"}
    SIG{"Signature valid?"}
    ISS{"iss matches expected issuer?"}
    AUD{"aud matches expected audience?"}
    TIME{"Time claims valid?"}
    CID{"cid matches allowed lab client?"}
    TRUST["TOKEN TRUSTED"]
    SCOPE{"employee.read in scp?"}

    R401["401 Unauthorized<br/>credential missing or invalid"]
    R403["403 Forbidden<br/>valid credential<br/>insufficient_scope"]
    R200["200 OK<br/>return employee data"]

    REQ --> PRESENT
    PRESENT -->|No| R401
    PRESENT -->|Yes| HEADER
    HEADER -->|No| R401
    HEADER -->|Yes| KEY
    KEY -->|No| R401
    KEY -->|Yes| SIG
    SIG -->|No| R401
    SIG -->|Yes| ISS
    ISS -->|No| R401
    ISS -->|Yes| AUD
    AUD -->|No| R401
    AUD -->|Yes| TIME
    TIME -->|No| R401
    TIME -->|Yes| CID
    CID -->|No| R401
    CID -->|Yes| TRUST
    TRUST --> SCOPE
    SCOPE -->|No| R403
    SCOPE -->|Yes| R200
~~~

The scope check is reached only after token validation succeeds.

## 4. Trusted issuer to signing key

**Question answered:** Where does the API get the public key used to verify the access token?

~~~mermaid
flowchart TB
    CFG["API CONFIGURATION<br/>Expected Custom AS issuer"]
    DISC["OIDC discovery document"]
    JWKS["Trusted jwks_uri"]
    HEADER["Access-token header<br/>kid"]
    KEY["Matching public key"]
    VERIFY["Verify JWT signature"]

    CFG --> DISC --> JWKS
    HEADER --> KEY
    JWKS --> KEY
    KEY --> VERIFY
~~~

Trust starts from API configuration, not from an arbitrary issuer value supplied by an untrusted token.

## 5. Audience validation

**Question answered:** What does aud mean from the resource-server perspective?

~~~mermaid
flowchart LR
    AS["Custom Authorization Server<br/>Audience setting"]
    TOKEN["Access token<br/>aud claim"]
    API["Employee API<br/>Expected audience"]
    CHECK{"Values match?"}
    PASS["Audience check passes"]
    FAIL["401 invalid_token"]

    AS --> TOKEN --> CHECK
    API --> CHECK
    CHECK -->|Yes| PASS
    CHECK -->|No| FAIL
~~~

The Day 8 API uses the actual audience configured on the default Custom Authorization Server.

## 6. Requested scope vs granted scope vs enforced scope

**Question answered:** Where does employee.read appear in the lifecycle?

~~~mermaid
flowchart LR
    CLIENT["Client requests<br/>employee.read"]
    POLICY["Custom AS policy/rule<br/>decides whether request can be granted"]
    TOKEN["Access token<br/>scp includes employee.read"]
    API["Employee API<br/>requires employee.read"]
    RESULT["Allow endpoint"]

    CLIENT --> POLICY --> TOKEN --> API --> RESULT
~~~

The API checks the granted scope in the validated token.

It does not trust what the client says it requested.

## 7. 401 vs 403

**Question answered:** Is the credential invalid, or is the trusted caller missing permission?

~~~mermaid
flowchart TB
    START["Protected API request"]
    VALID{"Acceptable bearer credential?"}
    PERM{"Required scope present?"}
    U401["401 Unauthorized<br/>No acceptable bearer credential"]
    F403["403 Forbidden<br/>Credential accepted<br/>Permission insufficient"]
    OK["200 OK"]

    START --> VALID
    VALID -->|No| U401
    VALID -->|Yes| PERM
    PERM -->|No| F403
    PERM -->|Yes| OK
~~~

This is the distinction the learner should be able to explain in one sentence.

## 8. Why an ID token fails at the API

**Question answered:** Why can a valid ID token still be rejected as an API credential?

~~~mermaid
flowchart LR
    IDT["ID token<br/>aud = OIDC client"]
    API["Employee API<br/>expects API audience"]
    CHECK{"Audience and token purpose<br/>acceptable for API?"}
    FAIL["Reject<br/>401 invalid_token"]

    IDT --> CHECK
    API --> CHECK
    CHECK -->|No| FAIL
~~~

A token can be valid for one purpose and still be wrong for another consumer.

## 9. Safe troubleshooting evidence

**Question answered:** How can we diagnose API failures without logging credentials?

~~~mermaid
flowchart LR
    CLIENT["Postman or client response<br/>HTTP status<br/>WWW-Authenticate<br/>X-Correlation-ID"]
    LOG["API log<br/>same correlation ID<br/>validation stage<br/>safe reason category"]
    OKTA["Okta evidence<br/>token issuance / System Log<br/>when relevant"]

    CLIENT --> DIAG["Correlate evidence"]
    LOG --> DIAG
    OKTA --> DIAG
~~~

Never add the raw bearer token to diagnostic logs.

## 10. Local validation vs live revocation state

**Question answered:** What does Day 8 validation prove, and what does it not prove?

~~~mermaid
flowchart TB
    TOKEN["JWT access token"]
    LOCAL["Local validation<br/>signature + issuer + audience + time + cid"]
    TRUST["Token is locally valid"]
    Q["Does this prove the token<br/>has not been revoked right now?"]
    NO["No<br/>Revocation/introspection is a separate topic"]

    TOKEN --> LOCAL --> TRUST --> Q --> NO
~~~

Day 10 adds revocation and introspection.
