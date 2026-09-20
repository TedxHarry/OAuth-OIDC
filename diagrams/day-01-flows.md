# Day 1 Flow Diagrams

These diagrams support the Day 1 lesson. They are intentionally simple. Day 2 and Day 3 add the detailed HTTP and Authorization Code + PKCE transactions.

## 1. Authentication and API authorization are separate problems

**Question answered:** Which part of the requirement is user authentication, and which part is API authorization?

```mermaid
flowchart LR
    U[Employee] --> C[Employee Portal]
    C -->|Sign-in request| O[Okta]
    O -->|Authentication result and ID token| C
    C -->|Access token| A[Employee API]
    A -->|Protected data| C
```

Read it in two parts:

```text
Employee -> Portal -> Okta
Authentication

Portal -> Employee API
API authorization
```

## 2. Who consumes which token

**Question answered:** Which component is supposed to consume the ID token, and which component receives the access token?

```mermaid
flowchart TB
    O[Okta] -->|ID token| C[Client application]
    O -->|Access token| C
    C -->|Bearer access token| A[Resource server / API]

    I[ID token purpose] --> C
    X[Access token purpose] --> A
```

Working rule:

```text
ID token
-> consumed by the client application

Access token
-> presented to the resource server / API
```

## 3. Public client and confidential client

**Question answered:** Can the application component protect a client credential from the end user?

```mermaid
flowchart LR
    subgraph Public_Client
        B[Browser] --> R[React SPA]
        R --> P[Cannot safely keep a client secret]
    end

    subgraph Confidential_Client
        U[Browser] --> J[Server-side Java application]
        J --> S[Credential kept on controlled server infrastructure]
    end

    P --> PKCE[Authorization Code + PKCE]
    S --> CA[Client authentication at token endpoint]
```

The deciding question is:

> Can this component actually protect the credential from the end user?

## 4. User-facing application path

**Question answered:** What is the high-level path when a human user signs in and the application later calls an API?

```mermaid
sequenceDiagram
    participant U as Employee
    participant C as Employee Portal
    participant O as Okta
    participant A as Employee API

    U->>C: Open Employee Portal
    C->>O: Start sign-in
    O->>U: Authenticate user
    U->>O: Complete authentication
    O-->>C: Authentication result and tokens
    C->>A: API request with access token
    A-->>C: Protected response
```

Day 3 expands the sign-in portion into the actual Authorization Code + PKCE transaction.

## 5. Scheduled service path

**Question answered:** What changes when a service calls the API without a human user?

```mermaid
sequenceDiagram
    participant J as Scheduled Python Job
    participant O as Okta
    participant A as Employee API

    J->>O: Authenticate as the service
    O-->>J: Access token
    J->>A: API request with access token
    A-->>J: Protected response
```

There is no employee browser session in this path.

```text
No human user
No interactive login
No ID token
Access token used for API access
```

Day 11 implements this using Client Credentials.

## 6. Know where OAuth/OIDC stops

**Question answered:** Which requirement belongs to OAuth/OIDC, and which requirement belongs to account provisioning/lifecycle?

```mermaid
flowchart TB
    R[Application requirements]
    R --> OIDC[User authentication / SSO]
    R --> OA[API authorization]
    R --> P[Account provisioning and lifecycle]

    OIDC --> O[OIDC]
    OA --> OAuth[OAuth 2.0]
    P --> SCIM[SCIM or application API]
```

A successful OIDC login does not by itself create, update, disable, or delete the downstream account.
