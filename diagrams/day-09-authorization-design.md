# Day 9 Flow Diagrams

These diagrams support the Day 9 lesson.

Each diagram answers one authorization-design question.

## 1. Audience, scope, and claim answer different questions

**Question answered:** What does each token concept represent?

~~~mermaid
flowchart TB
    TOKEN["ACCESS TOKEN"]

    AUD["aud<br/>WHO is this token for?<br/><br/>api://employee-service"]
    SCP["scp<br/>WHAT API permissions were granted?<br/><br/>employee.read<br/>salary.read"]
    CLAIM["custom claims<br/>WHAT contextual facts travel with it?<br/><br/>department<br/>groups"]

    TOKEN --> AUD
    TOKEN --> SCP
    TOKEN --> CLAIM
~~~

Do not use these terms interchangeably.

## 2. Dedicated Employee API authorization boundary

**Question answered:** How does one authorization server protect an API product with multiple operations?

~~~mermaid
flowchart LR
    SPA["Employee Portal SPA"]
    AS["Employee API Authorization Server<br/><br/>audience = api://employee-service"]
    TOKEN["Access Token"]
    API["Employee API"]

    EMP["GET /api/employees<br/>requires employee.read"]
    SAL["GET /api/salary<br/>requires salary.read"]

    SPA -->|"Request custom scopes"| AS
    AS -->|"Issue token when policy allows"| TOKEN
    TOKEN -->|"Bearer token"| API
    API --> EMP
    API --> SAL
~~~

The authorization-server boundary represents the Employee API product.

Scopes distinguish operations inside it.

## 3. Requested, permitted, granted, enforced

**Question answered:** How does salary.read move from a client request to an API authorization decision?

~~~mermaid
flowchart TB
    REQUEST["1. CLIENT REQUESTS<br/>salary.read"]
    POLICY["2. AUTHORIZATION SERVER<br/>Policy covers client?"]
    RULE["3. RULE EVALUATION<br/>User/group + grant + scopes"]
    PERMIT{"4. Rule permits<br/>salary.read?"}
    FAIL["Authorization fails<br/>No salary token issued"]
    TOKEN["5. ACCESS TOKEN<br/>scp contains salary.read"]
    API["6. EMPLOYEE API<br/>/api/salary requires salary.read"]
    ALLOW["7. Request allowed"]

    REQUEST --> POLICY --> RULE --> PERMIT
    PERMIT -->|No| FAIL
    PERMIT -->|Yes| TOKEN --> API --> ALLOW
~~~

The HR group does not insert salary.read by itself.

## 4. HR rule vs employee rule

**Question answered:** How does the same SPA receive different permissions for different users or requests?

~~~mermaid
flowchart TB
    REQ["Authorization request<br/>from Employee Portal SPA"]
    HRQ{"User in<br/>Employee-API-HR?"}
    HRSCOPE{"Requested custom scopes<br/>fit HR rule?"}
    HR["HR Salary Access<br/>employee.read + salary.read<br/>15-minute access token"]

    EMPQ{"Requested custom scopes<br/>fit employee rule?"}
    EMP["Employee Read Access<br/>employee.read<br/>60-minute access token"]

    DENY["No matching allow rule<br/>Authorization fails"]

    REQ --> HRQ
    HRQ -->|Yes| HRSCOPE
    HRSCOPE -->|Yes| HR
    HRSCOPE -->|No| EMPQ
    HRQ -->|No| EMPQ
    EMPQ -->|Yes| EMP
    EMPQ -->|No| DENY
~~~

The rule conditions determine whether a request is allowed.

## 5. First matching rule wins

**Question answered:** Why can a broad earlier rule defeat a carefully designed later rule?

~~~mermaid
flowchart TB
    REQ["HR user requests salary.read"]
    R1{"Priority 1<br/>Temporary Broad Rule<br/>Any user + Any scopes"}
    BROAD["MATCH<br/>60-minute token"]
    STOP["STOP<br/>No later rules evaluated"]

    R2["Priority 2<br/>HR Salary Access<br/>15-minute token"]

    REQ --> R1
    R1 -->|Matches| BROAD --> STOP
    STOP -. "HR rule never reached" .-> R2
~~~

Priority changes behavior.

A broad rule is not harmless just because a specific rule exists later.

## 6. Group membership does not inject a scope

**Question answered:** What happens when an HR user does not request salary.read?

~~~mermaid
flowchart LR
    HR["User belongs to<br/>Employee-API-HR"]
    REQUEST["SPA requests<br/>openid + employee.read"]
    RULE["Matching rule evaluates<br/>requested scopes"]
    TOKEN["Token scp<br/>openid + employee.read"]
    ABSENT["salary.read<br/>ABSENT"]

    HR --> RULE
    REQUEST --> RULE
    RULE --> TOKEN --> ABSENT
~~~

Membership can affect rule eligibility.

It does not silently add an unrequested custom scope.

## 7. Claims are separate from permission

**Question answered:** How do department and groups relate to salary.read?

~~~mermaid
flowchart TB
    PROFILE["User Profile<br/>department = HR"]
    GROUP["Group Membership<br/>Employee-API-HR"]

    CLAIM1["Access-token claim<br/>department = HR"]
    CLAIM2["Access-token claim<br/>groups = Employee-API-HR"]

    POLICY["Policy rule uses<br/>Employee-API-HR condition"]
    SCOPE["Granted permission<br/>salary.read"]
    API["/api/salary<br/>requires salary.read"]

    PROFILE --> CLAIM1
    GROUP --> CLAIM2
    GROUP --> POLICY --> SCOPE --> API

    CLAIM1 -. "context only in this design" .-> API
    CLAIM2 -. "context only in this design" .-> API
~~~

Our first implementation authorizes salary access with salary.read.

## 8. Scope-conditioned claim inclusion

**Question answered:** Why can department appear in one access token and not another?

~~~mermaid
flowchart TB
    CLAIM["department claim configuration<br/><br/>Token type: Access Token<br/>Expression: user.department<br/>Include in: salary.read"]
    TOKEN1["Token A<br/>scp includes salary.read"]
    TOKEN2["Token B<br/>scp does not include salary.read"]

    YES["department included"]
    NO["department absent"]

    CLAIM --> TOKEN1 --> YES
    CLAIM --> TOKEN2 --> NO
~~~

Claim inclusion is configuration.

It is not proof of permission by itself.

## 9. Access-token claim vs ID-token claim

**Question answered:** Why do our custom claims not automatically appear in the ID token?

~~~mermaid
flowchart LR
    CONFIG["Claim configuration<br/>Include in token type:<br/>Access Token"]
    AT["Access Token"]
    ID["ID Token"]

    CONFIG -->|"Included when other conditions match"| AT
    CONFIG -. "Not automatically included" .-> ID
~~~

Choose the token type based on the intended consumer.

## 10. Token Preview vs real flow

**Question answered:** What can Token Preview prove, and what still needs an end-to-end test?

~~~mermaid
flowchart LR
    PREVIEW["TOKEN PREVIEW<br/><br/>client<br/>grant type<br/>user<br/>scopes"]
    PCAN["Can prove/configure<br/>rule result<br/>claims<br/>scope result<br/>token lifetime"]

    REAL["REAL AUTHORIZATION CODE FLOW"]
    RCAN["Also proves<br/>redirect URI<br/>PKCE<br/>callback<br/>client behavior<br/>real token issuance"]

    API["EMPLOYEE API CALL"]
    ACAN["Proves<br/>resource-server validation<br/>endpoint scope enforcement"]

    PREVIEW --> PCAN
    REAL --> RCAN
    API --> ACAN
~~~

Use the three together when debugging a complete implementation.

## 11. Authentication policy vs API access policy

**Question answered:** Which policy layer should you investigate?

~~~mermaid
flowchart TB
    ISSUE["Observed problem"]

    AUTH["AUTHENTICATION / SESSION POLICY<br/><br/>MFA<br/>reauthentication<br/>assurance<br/>Okta session"]
    API["CUSTOM AUTHORIZATION SERVER POLICY<br/><br/>client<br/>grant type<br/>user/group<br/>requested scopes<br/>token lifetime"]

    Q{"What is wrong?"}

    ISSUE --> Q
    Q -->|"Unexpected MFA or sign-in requirement"| AUTH
    Q -->|"Missing scope, wrong rule, token lifetime"| API
~~~

Do not change API access-policy rules to fix an authentication-policy problem.

## 12. Complete HR salary path

**Question answered:** What is the complete sequence from request to protected salary data?

~~~mermaid
sequenceDiagram
    autonumber
    actor U as HR Employee
    participant C as Employee Portal SPA
    participant A as Employee API Authorization Server
    participant API as Employee API

    C->>A: /authorize<br/>openid + employee.read + salary.read
    A->>U: Authenticate when required
    U->>A: Complete authentication

    Note over A: Evaluate policy for SPA
    Note over A: First matching rule:<br/>HR Salary Access
    Note over A: User in Employee-API-HR<br/>salary.read permitted

    A-->>C: Authorization code
    C->>A: /token<br/>code + PKCE verifier
    A-->>C: Access token<br/>aud=api://employee-service<br/>scp includes salary.read<br/>department/groups claims

    C->>API: GET /api/salary<br/>Bearer access token

    Note over API: Validate signature, issuer,<br/>audience, time, client

    Note over API: Require salary.read

    API-->>C: 200 salary response
~~~

Every component has a specific responsibility.

## 13. Non-HR salary request

**Question answered:** Where should an ineligible salary request stop?

~~~mermaid
flowchart TB
    REQ["Non-HR user requests salary.read"]
    HR["HR Salary Access rule"]
    HRFAIL["Group condition does not match"]
    EMP["Employee Read Access rule"]
    SCOPEFAIL["salary.read is not allowed"]
    NONE["No matching allow rule"]
    FAIL["Authorization fails<br/>No valid salary token minted"]

    REQ --> HR --> HRFAIL --> EMP --> SCOPEFAIL --> NONE --> FAIL
~~~

The API does not need to receive a valid salary token for this denied issuance case.
