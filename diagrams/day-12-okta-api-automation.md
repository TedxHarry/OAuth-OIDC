# Day 12 Flow Diagrams

These diagrams support the Day 12 lesson.

Each diagram answers one Okta API automation question.

## 1. Day 11 vs Day 12

**Question answered:** Why does another Client Credentials flow use a different authorization design?

~~~mermaid
flowchart TB
    subgraph D11["DAY 11 - YOUR API"]
        C1["Employee Reporting Service"]
        A1["Employee API Custom Authorization Server"]
        S1["employee.report.read"]
        M1["client_secret_basic"]
        R1["Employee API"]

        C1 --> M1 --> A1 --> S1 --> R1
    end

    subgraph D12["DAY 12 - OKTA APIs"]
        C2["Okta Management Automation"]
        A2["Org Authorization Server"]
        S2["okta.* scopes"]
        M2["private_key_jwt"]
        R2["Okta Management APIs"]

        C2 --> M2 --> A2 --> S2 --> R2
    end
~~~

The grant is the same. The protected resource and authorization model are different.

## 2. Public key vs private key

**Question answered:** Which key goes where?

~~~mermaid
flowchart LR
    AUTO["Automation"]
    PRIV["PRIVATE KEY<br/>stays with automation"]
    ASSERT["Sign client assertion"]

    OKTA["Okta service app"]
    PUB["PUBLIC JWK<br/>registered with Okta"]
    VERIFY["Verify assertion signature"]

    AUTO --> PRIV --> ASSERT
    OKTA --> PUB --> VERIFY

    ASSERT -->|"signed JWT"| VERIFY
~~~

Never commit the private key.

## 3. Client assertion vs access token

**Question answered:** What are the two JWT-like credentials doing?

~~~mermaid
sequenceDiagram
    autonumber
    participant S as Automation
    participant O as Org Authorization Server
    participant API as Okta Management API

    Note over S: Build short-lived client assertion<br/>iss=sub=client_id<br/>aud=Org AS token endpoint<br/>kid=registered key

    S->>O: POST /oauth2/v1/token<br/>client_assertion + requested okta.* scopes

    Note over O: Verify private_key_jwt
    Note over O: Check requested scopes against app grants

    O-->>S: Okta API access token

    S->>API: GET /api/v1/users<br/>Authorization: Bearer access token

    Note over API: Evaluate OAuth scope<br/>and service app admin authorization

    API-->>S: Management API response
~~~

The assertion authenticates the client. The access token authorizes the API call.

## 4. private_key_jwt assertion contents

**Question answered:** What must the assertion say?

~~~mermaid
flowchart TB
    JWT["CLIENT ASSERTION"]

    HEADER["HEADER<br/>alg = RS256<br/>kid = registered key"]
    ISS["iss = client_id"]
    SUB["sub = client_id"]
    AUD["aud = exact Org AS token endpoint"]
    IAT["iat = now"]
    EXP["exp = short future time"]
    JTI["jti = unique identifier"]

    JWT --> HEADER
    JWT --> ISS
    JWT --> SUB
    JWT --> AUD
    JWT --> IAT
    JWT --> EXP
    JWT --> JTI
~~~

For this flow the assertion audience is the token endpoint, not the Management API endpoint.

## 5. Scope grant plus admin authorization

**Question answered:** Why can token acquisition succeed while the API call fails?

~~~mermaid
flowchart TB
    REQUEST["Request okta.users.read"]
    GRANT{"Scope granted to<br/>service app?"}
    NO_TOKEN["No usable token for request"]
    TOKEN["Access token issued<br/>scope response includes okta.users.read"]

    ROLE{"Service app admin role<br/>permits operation?"}
    RESOURCE{"Target resource<br/>within authorization?"}

    DENY["Management API denies operation"]
    ALLOW["Management API allows operation"]

    REQUEST --> GRANT
    GRANT -->|No| NO_TOKEN
    GRANT -->|Yes| TOKEN --> ROLE
    ROLE -->|No| DENY
    ROLE -->|Yes| RESOURCE
    RESOURCE -->|No| DENY
    RESOURCE -->|Yes| ALLOW
~~~

A scope grant is not a replacement for administrative authorization.

## 6. Read-only first design

**Question answered:** What is the safe Day 12 starting point?

~~~mermaid
flowchart LR
    APP["Okta Management Automation"]

    SCOPES["Granted scopes<br/>okta.users.read<br/>okta.groups.read"]

    ROLE["Admin role<br/>Read-only Administrator"]

    API["Allowed learning operations<br/>List users<br/>Get test user<br/>List groups"]

    APP --> SCOPES
    APP --> ROLE
    SCOPES --> API
    ROLE --> API
~~~

Start with read-only access before adding write permissions.

## 7. Optional targeted group write

**Question answered:** How can a service receive write capability without broad org-wide power?

~~~mermaid
flowchart TB
    APP["Service app"]

    SCOPE["OAuth scope<br/>okta.groups.manage"]
    ROLE["Admin role<br/>Group Membership Administrator<br/>or equivalent narrow custom role"]
    TARGET["Target<br/>OAuth-Day12-Test-Group"]

    CALL["PUT group membership request"]

    ALLOW["Allowed only when<br/>scope + role + target match"]
    DENY["Other group target<br/>denied"]

    APP --> SCOPE
    APP --> ROLE --> TARGET

    SCOPE --> CALL
    TARGET --> CALL

    CALL --> ALLOW
    TARGET -. "does not include other group" .-> DENY
~~~

Resource targeting can narrow an administrative role.

## 8. Three failure layers

**Question answered:** Where did the automation fail?

~~~mermaid
flowchart TB
    START["Automation request"]

    T{"Did /oauth2/v1/token<br/>return an access token?"}
    AUTHN["LAYER 1<br/>CLIENT AUTHENTICATION<br/><br/>private key<br/>kid<br/>iss/sub<br/>aud<br/>exp<br/>jti"]

    SCOPE["LAYER 2<br/>SCOPE GRANT<br/><br/>scope supported?<br/>scope granted to app?"]

    APIQ{"Did Management API<br/>allow operation?"}

    AUTHZ["LAYER 3<br/>ADMIN AUTHORIZATION<br/><br/>admin role<br/>permission<br/>resource target<br/>resource set"]

    OK["Operation succeeds"]

    START --> T
    T -->|"No, client assertion rejected"| AUTHN
    T -->|"No, scope request rejected"| SCOPE
    T -->|Yes| APIQ
    APIQ -->|No| AUTHZ
    APIQ -->|Yes| OK
~~~

If the token exists, do not start by rebuilding the key pair.

## 9. Wrong assertion audience

**Question answered:** Why is the token endpoint the assertion audience?

~~~mermaid
flowchart LR
    ASSERT["Client assertion"]
    RIGHT["aud = https://org/oauth2/v1/token"]
    WRONG1["aud = /oauth2/default/v1/token"]
    WRONG2["aud = /api/v1/users"]

    TOKEN["Org AS /token"]

    ASSERT --> RIGHT -->|"matches authentication target"| TOKEN
    ASSERT --> WRONG1 -->|"wrong authorization server"| FAIL["Rejected"]
    ASSERT --> WRONG2 -->|"API is not client-auth target"| FAIL
~~~

## 10. Scope grant without admin role

**Question answered:** What does a successful token prove?

~~~mermaid
sequenceDiagram
    participant S as Service App
    participant O as Org Authorization Server
    participant A as Okta Management API

    S->>O: Request granted scope okta.users.read
    O-->>S: Access token issued

    Note over S,O: Token issuance proves the scope was granted to the app

    S->>A: GET /api/v1/users<br/>Bearer token

    Note over A: Service app lacks required admin authorization

    A-->>S: Authorization denied
~~~

The token can contain the requested scope and still lack the administrative capability.

## 11. Access-token caching

**Question answered:** What should be cached, and what should be recreated?

~~~mermaid
flowchart TB
    NEED["Need Okta API access"]
    CACHE{"Cached access token<br/>still safely valid?"}
    USE["Reuse access token"]
    ASSERT["Create NEW short-lived<br/>client assertion"]
    TOKEN["POST /oauth2/v1/token<br/>get new access token"]
    API["Call Okta Management API"]

    NEED --> CACHE
    CACHE -->|Yes| USE --> API
    CACHE -->|No| ASSERT --> TOKEN --> API
~~~

Cache the access token. Recreate the assertion for each token request.

## 12. Signing-key rotation

**Question answered:** How do you rotate without an outage?

~~~mermaid
flowchart LR
    A["Key A active"]
    BGEN["Generate key B"]
    BPUB["Register public key B in Okta"]
    BDEPLOY["Deploy private key B"]
    BTEST["Sign with kid B<br/>prove token acquisition"]
    AREMOVE["Retire public key A"]

    A --> BGEN --> BPUB --> BDEPLOY --> BTEST --> AREMOVE
~~~

Use an overlap period. Do not delete the old public key before the automation has moved to the new private key.
