# Day 11 Flow Diagrams

These diagrams support the Day 11 lesson.

Each diagram answers one machine-to-machine OAuth question.

## 1. User flow vs machine flow

**Question answered:** What disappears when no human user is involved?

~~~mermaid
flowchart TB
    subgraph USER["USER-DELEGATED FLOW"]
        U["Human user"]
        SPA["Browser SPA"]
        AUTH["/authorize"]
        CODE["Authorization Code"]
        TOKEN1["Access token"]
        U --> SPA --> AUTH --> CODE --> TOKEN1
    end

    subgraph MACHINE["CLIENT CREDENTIALS FLOW"]
        SVC["Reporting Service"]
        TOKENEP["/token"]
        TOKEN2["Access token"]
        SVC -->|"Client authentication"| TOKENEP --> TOKEN2
    end
~~~

Client Credentials has no browser, user login, authorization code, or PKCE transaction.

## 2. Complete Client Credentials transaction

**Question answered:** Who talks to whom, in what order?

~~~mermaid
sequenceDiagram
    autonumber
    participant S as Employee Reporting Service
    participant A as Employee API Authorization Server
    participant API as Employee API

    S->>A: POST /token<br/>Basic client authentication<br/>grant_type=client_credentials<br/>scope=employee.report.read

    Note over A: Authenticate OAuth client
    Note over A: Evaluate service access policy
    Note over A: Grant = Client Credentials
    Note over A: User = No user
    Note over A: Scope permitted?

    A-->>S: Access token

    S->>API: GET /api/service-report<br/>Authorization: Bearer access_token

    Note over API: Validate signature, issuer,<br/>audience, time, cid

    Note over API: Require employee.report.read

    API-->>S: 200 report data
~~~

There is no interactive front channel.

## 3. Client authentication vs API authorization

**Question answered:** What does the client secret prove, and what does it not prove?

~~~mermaid
flowchart LR
    CREDS["Client ID + Client Secret"]
    TOKENEP["TOKEN ENDPOINT"]
    AUTHN["CLIENT AUTHENTICATION<br/>Is this the registered service?"]

    TOKEN["Access token<br/>scp = employee.report.read"]
    API["Employee API"]
    AUTHZ["API AUTHORIZATION<br/>Does token grant the endpoint scope?"]

    CREDS --> TOKENEP --> AUTHN --> TOKEN --> API --> AUTHZ
~~~

A valid client secret does not grant every API operation.

## 4. Service-specific access policy

**Question answered:** What must match before Okta can issue the machine token?

~~~mermaid
flowchart TB
    REQ["Token request"]
    CLIENT{"Policy assigned to<br/>Employee Reporting Service?"}
    GRANT{"Grant type<br/>Client Credentials?"}
    USER{"User condition<br/>No user?"}
    SCOPE{"Requested scope<br/>employee.report.read allowed?"}
    ISSUE["Issue access token"]
    FAIL["Token request fails"]

    REQ --> CLIENT
    CLIENT -->|No| FAIL
    CLIENT -->|Yes| GRANT
    GRANT -->|No| FAIL
    GRANT -->|Yes| USER
    USER -->|No| FAIL
    USER -->|Yes| SCOPE
    SCOPE -->|No| FAIL
    SCOPE -->|Yes| ISSUE
~~~

Client Credentials needs a rule that can match a request with no user.

## 5. Why No user matters

**Question answered:** Why can a normal user-oriented rule fail for a service app?

~~~mermaid
flowchart LR
    CC["Client Credentials request"]
    FACT["No human user exists"]

    WRONG["User condition:<br/>Any user assigned the app"]
    RIGHT["User condition:<br/>No user"]

    FAIL["Cannot represent the<br/>machine-only transaction"]
    MATCH["Rule can match<br/>service transaction"]

    CC --> FACT
    FACT --> WRONG --> FAIL
    FACT --> RIGHT --> MATCH
~~~

Do not invent a user just to satisfy a rule.

## 6. Requested, permitted, granted for a machine client

**Question answered:** Does a valid secret automatically grant the requested service scope?

~~~mermaid
flowchart TB
    REQUEST["Service requests<br/>employee.report.read"]
    AUTHN["Client authentication succeeds"]
    POLICY["Service policy/rule evaluates request"]
    PERMIT{"Scope permitted?"}
    DENY["Token request fails"]
    TOKEN["Access token<br/>scp contains employee.report.read"]

    REQUEST --> AUTHN --> POLICY --> PERMIT
    PERMIT -->|No| DENY
    PERMIT -->|Yes| TOKEN
~~~

Client authentication and scope authorization are separate.

## 7. Service scope vs user scopes

**Question answered:** Why create employee.report.read?

~~~mermaid
flowchart TB
    API["Employee API"]

    EMP["/api/employees<br/>employee.read<br/>user-facing"]
    SAL["/api/salary<br/>salary.read<br/>HR user"]
    REP["/api/service-report<br/>employee.report.read<br/>machine service"]

    API --> EMP
    API --> SAL
    API --> REP
~~~

Distinct scopes make intended operations and callers easier to review.

## 8. No OpenID objects in the service flow

**Question answered:** Which earlier OAuth/OIDC concepts do not belong in Client Credentials?

~~~mermaid
flowchart TB
    CC["Client Credentials"]

    NO1["No browser"]
    NO2["No /authorize"]
    NO3["No user login"]
    NO4["No state / nonce"]
    NO5["No PKCE"]
    NO6["No authorization code"]
    NO7["No ID token"]
    NO8["No UserInfo"]
    NO9["No user refresh-token pattern"]

    CC --> NO1
    CC --> NO2
    CC --> NO3
    CC --> NO4
    CC --> NO5
    CC --> NO6
    CC --> NO7
    CC --> NO8
    CC --> NO9
~~~

Do not carry user-flow components into a machine flow without a requirement.

## 9. Token caching and renewal

**Question answered:** When should the service obtain another access token?

~~~mermaid
flowchart TB
    NEED["Service needs API access"]
    CACHE{"Cached token exists?"}
    TIME{"Token safely before expiry?"}
    GET["Authenticate client<br/>and request new token"]
    USE["Reuse cached access token"]
    API["Call Employee API"]

    NEED --> CACHE
    CACHE -->|No| GET --> API
    CACHE -->|Yes| TIME
    TIME -->|Yes| USE --> API
    TIME -->|No| GET
~~~

Do not request a new token for every API call when one safely reusable token is already available.

## 10. Failure classification

**Question answered:** Which layer failed?

~~~mermaid
flowchart TB
    FAIL["Machine integration failure"]

    Q1{"Did /token return<br/>an access token?"}
    CLIENT["Client authentication / token issuance<br/>invalid_client, wrong scope,<br/>policy/grant/No-user mismatch"]

    Q2{"Did API accept<br/>the bearer token?"}
    API401["API token validation<br/>401"]
    Q3{"Required endpoint<br/>scope present?"}
    API403["API authorization<br/>403"]
    OK["API request allowed"]

    FAIL --> Q1
    Q1 -->|No| CLIENT
    Q1 -->|Yes| Q2
    Q2 -->|No| API401
    Q2 -->|Yes| Q3
    Q3 -->|No| API403
    Q3 -->|Yes| OK
~~~

Do not troubleshoot the client secret when the API already accepted the token.

## 11. Day 11 vs Day 12

**Question answered:** Why should you not copy the Day 11 token request into Okta Management API automation?

~~~mermaid
flowchart TB
    D11["DAY 11<br/>Our Employee API"]
    D11AS["Custom Authorization Server"]
    D11AUTH["client_secret_basic"]
    D11SCOPE["employee.report.read"]
    D11API["Employee API"]

    D12["DAY 12<br/>Okta Management APIs"]
    D12AS["Org Authorization Server"]
    D12AUTH["private_key_jwt"]
    D12SCOPE["okta.* scopes<br/>+ admin role/resource"]
    D12API["Okta APIs"]

    D11 --> D11AS --> D11AUTH --> D11SCOPE --> D11API
    D12 --> D12AS --> D12AUTH --> D12SCOPE --> D12API
~~~

Both use Client Credentials, but they authorize different resources with different Okta configurations.
