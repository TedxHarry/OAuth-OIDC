# Day 10 Flow Diagrams

These diagrams support the Day 10 lesson.

Each diagram answers one lifecycle question.

## 1. Five different pieces of state

**Question answered:** What exactly can still exist after someone says "I logged out"?

~~~mermaid
flowchart TB
    USER["One signed-in user"]

    OKTA["1. OKTA BROWSER SESSION<br/>Stored by Okta in browser<br/>Enables SSO"]
    APP["2. APPLICATION SESSION<br/>Owned by your app<br/>Example: opaque app cookie"]
    ID["3. ID TOKEN<br/>Authentication result<br/>Consumed by OIDC client"]
    AT["4. ACCESS TOKEN<br/>API credential<br/>Presented to resource server"]
    RT["5. REFRESH TOKEN<br/>Renewal credential<br/>Presented to authorization server"]

    USER --> OKTA
    USER --> APP
    USER --> ID
    USER --> AT
    USER --> RT
~~~

They have related origins but independent lifecycle behavior.

## 2. Local logout followed by immediate SSO

**Question answered:** Why can a user click Logout and appear signed in again immediately?

~~~mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant B as Browser
    participant APP as Web Application
    participant O as Okta

    U->>APP: Click local logout
    APP-->>B: Delete local application session
    Note over B,APP: App session is gone

    B->>APP: Open protected page
    APP-->>B: Redirect to Okta /authorize
    B->>O: /authorize

    Note over O: Existing Okta browser session<br/>can still be active

    O-->>B: Authorization response<br/>without another credential prompt when policy allows
    B->>APP: Callback
    APP-->>B: Create new local application session
~~~

Local logout can be successful even when Okta SSO remains active.

## 3. Okta browser-session logout

**Question answered:** What does the OIDC end-session flow actually change?

~~~mermaid
sequenceDiagram
    autonumber
    participant APP as Application
    participant B as Browser
    participant O as Okta
    participant POST as Registered post-logout URI

    Note over APP: Read ID token hint if needed
    Note over APP: Destroy local app session

    APP-->>B: Redirect to end_session_endpoint
    B->>O: Logout request<br/>id_token_hint + post_logout_redirect_uri + state

    Note over O: End Okta browser session

    O-->>B: Redirect to registered post-logout URI
    B->>POST: GET logged-out route
~~~

Token revocation is a separate control.

## 4. UserInfo

**Question answered:** How does the OIDC client obtain claims authorized by profile and email scopes?

~~~mermaid
sequenceDiagram
    participant C as OIDC Client
    participant U as Okta /userinfo

    C->>U: GET /userinfo<br/>Authorization: Bearer access_token

    Note over U: Evaluate active access token<br/>and granted OIDC scopes

    U-->>C: User claims allowed by scopes
~~~

The Employee API is not the UserInfo endpoint.

## 5. Refresh token lifecycle

**Question answered:** How can a SPA obtain new tokens without repeating browser sign-in?

~~~mermaid
sequenceDiagram
    participant SPA as Public SPA
    participant T as Authorization Server /token

    Note over SPA: Holds current refresh token

    SPA->>T: POST /token<br/>grant_type=refresh_token<br/>client_id + refresh_token

    Note over T: Validate refresh token

    T-->>SPA: New access token<br/>and current/new refresh token

    Note over SPA: Store the latest refresh token returned
~~~

For SPAs, Okta uses rotating refresh tokens by default when refresh tokens are enabled.

## 6. Access-token revocation

**Question answered:** What remains after only the access token is revoked?

~~~mermaid
flowchart LR
    REVOKE["Revoke ACCESS TOKEN"]
    AT["Access token<br/>inactive at authorization server"]
    RT["Refresh token<br/>still active"]
    NEW["Can obtain a new access token"]

    REVOKE --> AT
    REVOKE --> RT --> NEW
~~~

Access-token revocation does not revoke the associated refresh token.

## 7. Refresh-token revocation

**Question answered:** Why is refresh-token revocation broader?

~~~mermaid
flowchart LR
    REVOKE["Revoke REFRESH TOKEN"]
    RT["Refresh token<br/>revoked"]
    AT["Associated access token<br/>revoked at Okta"]
    REFRESH["Future refresh request<br/>fails"]

    REVOKE --> RT
    REVOKE --> AT
    RT --> REFRESH
~~~

## 8. Local JWT validation vs introspection

**Question answered:** Why can two valid checks report different results after revocation?

~~~mermaid
flowchart TB
    TOKEN["Same JWT access token"]

    LOCAL["LOCAL JWT VALIDATION<br/><br/>signature<br/>issuer<br/>audience<br/>exp<br/>cid<br/>scope"]
    LIVE["OKTA INTROSPECTION<br/><br/>current authorization-server<br/>active state"]

    LRESULT["Can still PASS<br/>while unexpired<br/>if only local checks are used"]
    IRESULT["Can return<br/>active = false<br/>after revocation"]

    TOKEN --> LOCAL --> LRESULT
    TOKEN --> LIVE --> IRESULT
~~~

The local validator has no live revocation fact unless the architecture supplies one.

## 9. The key Day 10 experiment

**Question answered:** What should happen before and after access-token revocation?

~~~mermaid
flowchart TB
    BEFORE["BEFORE REVOCATION"]
    BAPI["Employee API local JWT check<br/>200"]
    BINT["Okta introspection<br/>active = true"]

    REVOKE["Revoke access token"]

    AFTER["AFTER REVOCATION<br/>JWT still unexpired"]
    AAPI["Employee API local JWT check<br/>can still return 200"]
    AINT["Okta introspection<br/>active = false"]

    BEFORE --> BAPI
    BEFORE --> BINT
    BAPI --> REVOKE
    BINT --> REVOKE
    REVOKE --> AFTER
    AFTER --> AAPI
    AFTER --> AINT
~~~

This is not inconsistent. The two systems are checking different information.

## 10. Local removal vs server revocation

**Question answered:** What changes when the client merely clears its local token store?

~~~mermaid
flowchart LR
    CLEAR["Client clears local token storage"]
    LOCAL["Token no longer available<br/>to that local client state"]
    SERVER["Authorization-server token state<br/>not changed by local deletion alone"]

    CLEAR --> LOCAL
    CLEAR -. "No /revoke request" .-> SERVER
~~~

## 11. Expiration vs revocation

**Question answered:** What is the difference between a token expiring and being revoked?

~~~mermaid
flowchart TB
    TOKEN["Access token"]

    EXP["EXPIRATION<br/>Time reaches exp"]
    REV["REVOCATION<br/>Authorization server<br/>marks token inactive early"]

    LOCAL["Local validator can detect<br/>expiration from JWT exp"]
    LIVE["Introspection can observe<br/>server-side inactive state"]

    TOKEN --> EXP --> LOCAL
    TOKEN --> REV --> LIVE
~~~

## 12. Troubleshoot the correct lifecycle object

**Question answered:** Which evidence should you collect first?

~~~mermaid
flowchart TB
    ISSUE["Lifecycle complaint"]

    Q{"What is the actual symptom?"}

    LOCAL["App appears signed in/out<br/>Check application session"]
    SSO["Immediate SSO or re-prompt<br/>Check Okta browser session<br/>and auth policy"]
    CLAIM["Profile claim missing<br/>Check scopes + ID token/UserInfo"]
    API["API token behavior<br/>Check access token + local validation"]
    REFRESH["Renewal failed<br/>Check refresh token lifecycle"]
    REV["Revocation disagreement<br/>Compare introspection vs local validation"]

    ISSUE --> Q
    Q -->|"Local app state"| LOCAL
    Q -->|"Browser SSO behavior"| SSO
    Q -->|"User claims"| CLAIM
    Q -->|"API access"| API
    Q -->|"Token renewal"| REFRESH
    Q -->|"Revoked token still works"| REV
~~~

Name the object before changing configuration.
