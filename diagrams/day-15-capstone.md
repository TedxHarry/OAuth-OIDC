# Day 15 Capstone Diagrams

These diagrams support the Day 15 capstone.

The learner should first draw their own version before comparing.

## 1. Complete capstone architecture

**Question answered:** What are the major trust relationships?

~~~mermaid
flowchart LR
    USER["Employee"]
    SPA["React SPA<br/>Public OAuth/OIDC client"]
    OKTA["Okta"]
    CAS["Employee API<br/>Custom Authorization Server"]
    API["Java Employee API<br/>Resource Server"]
    JOB["Scheduled Reporting Service<br/>Confidential OAuth client"]
    OPS["Operations Automation<br/>OAuth service app"]
    ORGAS["Org Authorization Server"]
    OKTAAPI["Okta Management API"]

    USER -->|"uses browser"| SPA
    SPA -->|"Authorization Code + PKCE"| OKTA
    OKTA --> CAS
    SPA -->|"Bearer user access token"| API

    JOB -->|"Client Credentials"| CAS
    JOB -->|"Bearer machine access token"| API

    OPS -->|"Client Credentials + private_key_jwt"| ORGAS
    OPS -->|"Bearer Okta API access token"| OKTAAPI
~~~

The reporting service and Okta Management automation are different machine clients with different protected resources.

## 2. Human sign-in and API path

**Question answered:** How does an employee reach the Java API?

~~~mermaid
sequenceDiagram
    participant U as Employee
    participant SPA as React SPA
    participant O as Okta
    participant AS as Employee API Custom AS
    participant API as Java API

    U->>SPA: Open employee portal
    SPA->>SPA: Create state, nonce, PKCE verifier/challenge
    SPA->>O: /authorize with OIDC, API scopes, and offline_access when needed
    O->>U: Authenticate according to policy
    O-->>SPA: Authorization code + state
    SPA->>SPA: Validate state
    SPA->>AS: /token with code + PKCE verifier
    AS-->>SPA: ID token + access token + refresh token when applicable
    SPA->>API: GET /employees with Bearer access token
    API->>API: Validate JWT trust
    API->>API: Require employee.read
    API-->>SPA: 200 or authorization error
~~~

The API never trusts the browser merely because Okta authentication happened earlier.

## 3. HR salary authorization

**Question answered:** How does HR eligibility become an API permission?

~~~mermaid
flowchart TB
    REQ["React requests salary.read"]
    POLICY["Custom-AS access policy evaluates<br/>client + grant + user/group + requested scopes"]
    HR{"HR eligibility condition satisfied?"}
    TOKEN["Access token may contain salary.read"]
    API["Java API validates token"]
    SCOPE{"salary.read present?"}
    ALLOW["GET /salary -> 200"]
    DENY_AS["Authorization request/token issuance denied"]
    DENY_API["GET /salary -> 403"]

    REQ --> POLICY --> HR
    HR -->|No| DENY_AS
    HR -->|Yes| TOKEN --> API --> SCOPE
    SCOPE -->|Yes| ALLOW
    SCOPE -->|No| DENY_API
~~~

HR membership is an eligibility condition. salary.read is the API permission.

## 4. Employee scope vs contextual claims

**Question answered:** What belongs in a scope and what belongs in a claim?

~~~mermaid
flowchart LR
    FACT["Identity facts<br/>department<br/>groups<br/>employee type"]
    POLICY["Authorization policy"]
    SCOPE["API permission<br/>employee.read<br/>salary.read"]
    TOKEN["Validated access token"]
    API["Java API"]

    FACT --> POLICY
    POLICY -->|"permits requested scope"| SCOPE
    SCOPE --> TOKEN --> API
    FACT -->|"optional contextual claims"| TOKEN
~~~

A claim can provide context without becoming the API permission itself.

## 5. Scheduled service path

**Question answered:** How does the no-user reporting process authenticate and call the API?

~~~mermaid
sequenceDiagram
    participant JOB as Reporting Service
    participant AS as Employee API Custom AS
    participant API as Java API

    JOB->>AS: POST /token with client_credentials and employee.report.read
    AS->>AS: Validate client authentication
    AS->>AS: Match service policy: client + grant + No user + scope
    AS-->>JOB: Machine access token
    JOB->>API: GET /reports with Bearer machine token
    API->>API: Validate issuer, audience, signature, time, client boundary
    API->>API: Require employee.report.read
    API-->>JOB: 200 or 401/403
~~~

There is no human user, browser callback, state, nonce, or MFA step in this transaction.

## 6. Java API decision path

**Question answered:** What must happen before an endpoint scope is trusted?

~~~mermaid
flowchart TB
    REQUEST["Request with Bearer token"]
    PRESENT{"Bearer credential present?"}
    KEY{"Header/alg/kid acceptable<br/>and trusted JWKS key found?"}
    SIG{"Signature valid?"}
    ISS{"Issuer matches configured Custom AS?"}
    AUD{"Audience matches Employee API?"}
    TIME{"Token time claims valid?"}
    CLIENT{"Expected client boundary valid when required?"}
    TRUST["TOKEN TRUSTED"]
    PERM{"Required endpoint scope present?"}

    R401["401"]
    R403["403"]
    R200["200"]

    REQUEST --> PRESENT
    PRESENT -->|No| R401
    PRESENT -->|Yes| KEY
    KEY -->|No| R401
    KEY -->|Yes| SIG
    SIG -->|No| R401
    SIG -->|Yes| ISS
    ISS -->|No| R401
    ISS -->|Yes| AUD
    AUD -->|No| R401
    AUD -->|Yes| TIME
    TIME -->|No| R401
    TIME -->|Yes| CLIENT
    CLIENT -->|No| R401
    CLIENT -->|Yes| TRUST --> PERM
    PERM -->|No| R403
    PERM -->|Yes| R200
~~~

Validation comes before authorization.

## 7. Refresh and logout state

**Question answered:** Which state changes when the user logs out or refreshes?

~~~mermaid
flowchart TB
    SPA["React local auth state"]
    OKTASESSION["Okta browser session"]
    AT["Access token"]
    RT["Refresh token"]

    LOCAL["Local logout"]
    FULL["Full sign-out design"]
    REFRESH["Refresh flow"]

    LOCAL -->|"remove local state"| SPA
    FULL -->|"remove local state"| SPA
    FULL -->|"optionally end Okta session"| OKTASESSION
    FULL -->|"optionally revoke refresh capability"| RT

    RT --> REFRESH -->|"new access token and possibly rotated refresh token"| AT
    REFRESH --> RT
~~~

Define the desired behavior instead of assuming one logout operation changes every state.

## 8. Dev and prod isolation

**Question answered:** Why are environments independent trust systems?

~~~mermaid
flowchart LR
    DEV["DEVELOPMENT<br/>Dev Okta/app<br/>Dev issuer<br/>Dev client IDs<br/>Dev audience<br/>Dev API<br/>Dev secrets"]
    PROD["PRODUCTION<br/>Prod Okta/app<br/>Prod issuer<br/>Prod client IDs<br/>Prod audience<br/>Prod API<br/>Prod secrets"]

    BAD["Cross-environment pairing<br/>must be rejected"]

    DEV -. "Dev token to Prod API" .-> BAD
    PROD -. "Prod client with Dev secret/key" .-> BAD
~~~

The code may be identical. The trust configuration is not.

## 9. Future Okta Management automation

**Question answered:** Why is this different from the reporting service?

~~~mermaid
flowchart TB
    OPS["Operations Automation"]
    ASSERT["private_key_jwt<br/>client authentication"]
    ORGAS["Org Authorization Server"]
    GRANT["Granted okta.* scope"]
    TOKEN["Okta API access token"]
    API["Okta Management API"]
    ADMIN["Service-app admin role<br/>and resource authorization"]
    OK["Operation succeeds"]

    OPS --> ASSERT --> ORGAS --> GRANT --> TOKEN --> API --> ADMIN --> OK
~~~

The Employee API Custom Authorization Server is not part of this path.

## 10. Capstone troubleshooting map

**Question answered:** Where should investigation begin?

~~~mermaid
flowchart TB
    SYM["Observed failure"]
    BROWSER{"Browser authorization<br/>transaction involved?"}

    AUTHZ["Trace /authorize, authentication,<br/>callback, state, nonce"]
    TOKEN{"Was an access token issued?"}

    TOKENFAIL["Trace token endpoint<br/>client auth, grant, scope/policy"]
    API{"Resource response?"}

    U401["401<br/>token trust/validation"]
    U403["403<br/>resource permission"]
    OK["2xx<br/>next application/business layer"]

    SYM --> BROWSER
    BROWSER -->|Yes| AUTHZ --> TOKEN
    BROWSER -->|No| TOKEN
    TOKEN -->|No| TOKENFAIL
    TOKEN -->|Yes| API
    API -->|401| U401
    API -->|403| U403
    API -->|2xx| OK
~~~

The first failed layer determines what you inspect next.

## 11. Project evidence map

**Question answered:** Which evidence source proves which part?

~~~mermaid
flowchart TB
    INCIDENT["One capstone transaction"]

    BROWSER["Browser evidence<br/>Network / Console / storage"]
    CLIENT["Client evidence<br/>grant / scopes / token response"]
    TOKEN["Safe token evidence<br/>iss / aud / cid / scp / kid / exp"]
    API["Java API evidence<br/>status / challenge / correlation / validation stage"]
    OKTA["Okta evidence<br/>System Log / policy / app / service configuration"]

    PROOF["Correlated proof of<br/>last successful step<br/>first failed step<br/>root cause"]

    INCIDENT --> BROWSER
    INCIDENT --> CLIENT
    INCIDENT --> TOKEN
    INCIDENT --> API
    INCIDENT --> OKTA

    BROWSER --> PROOF
    CLIENT --> PROOF
    TOKEN --> PROOF
    API --> PROOF
    OKTA --> PROOF
~~~

No single evidence source proves the entire system.

## 12. Implementation handoff

**Question answered:** What should be left behind after the project?

~~~mermaid
flowchart LR
    REQ["Requirements and assumptions"]
    ARCH["Architecture and trust boundaries"]
    CONFIG["Environment configuration"]
    AUTHZ["Scopes / claims / policies"]
    API["API validation and authorization"]
    LIFE["Refresh / logout / rotation"]
    OPS["Monitoring / keys / secrets"]
    TEST["Acceptance and failure evidence"]
    HANDOFF["Operable project handoff"]

    REQ --> ARCH --> CONFIG --> AUTHZ --> API --> LIFE --> OPS --> TEST --> HANDOFF
~~~

A successful demo without an operable handoff is not the end of an implementation project.
