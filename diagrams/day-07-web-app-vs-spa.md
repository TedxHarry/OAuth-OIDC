# Day 7 Flow Diagrams

These diagrams support the Day 7 lesson.

Each diagram answers one architecture question.

## 1. Same user sign-in requirement, different OAuth client location

**Question answered:** Where does the OAuth/OIDC client actually run?

~~~mermaid
flowchart LR
    subgraph WEB["SERVER-SIDE WEB APPLICATION"]
        WB["Browser"]
        WS["Python Web Backend<br/>OAuth Client<br/>Confidential"]
        WO["Okta"]
        WB -->|"Browser request"| WS
        WS -->|"Redirect browser to sign in"| WB
        WB -->|"GET /authorize"| WO
        WO -->|"Redirect callback through browser"| WB
        WB -->|"GET /callback"| WS
    end

    subgraph SPA["BROWSER SPA"]
        SB["Browser JavaScript SPA<br/>OAuth Client<br/>Public"]
        SO["Okta"]
        SB -->|"GET /authorize"| SO
        SO -->|"Redirect callback"| SB
    end
~~~

The browser participates in both.

The OAuth client is **not** in the same place.

## 2. Server-side Web Application complete sign-in flow

**Question answered:** Who owns the transaction, calls /token, validates the ID token, and creates the local app session?

~~~mermaid
sequenceDiagram
    autonumber
    actor U as Employee
    participant B as Browser
    participant W as Python Web Backend<br/>Confidential OAuth Client
    participant A as Okta /authorize
    participant T as Okta /token

    U->>B: Open Web Application
    B->>W: GET /login

    Note over W: Create state + nonce + PKCE verifier<br/>Store them SERVER-SIDE

    W-->>B: 302 redirect to Okta /authorize
    B->>A: GET /authorize<br/>client_id + state + nonce + challenge

    A->>U: Show Okta-hosted sign-in when needed
    U->>A: Authenticate

    A-->>B: 302 to Web App callback<br/>code + state
    B->>W: GET /callback?code=...&state=...

    Note over W: Check state<br/>Recover server-side verifier

    W->>T: BACKEND POST /token<br/>client authentication + code + verifier
    T-->>W: ID token + access token

    Note over W: Validate ID token<br/>Store OAuth tokens SERVER-SIDE<br/>Create local application session

    W-->>B: Set-Cookie: day07_session=opaque-id<br/>HttpOnly + SameSite=Lax
    B->>W: Later request with application-session cookie
    W-->>B: Authenticated application page
~~~

**Important:** the browser does not perform the Web Application token request.

## 3. Browser SPA complete sign-in flow

**Question answered:** What moves into the browser when the SPA itself is the OAuth client?

~~~mermaid
sequenceDiagram
    autonumber
    actor U as Employee
    participant S as Browser SPA<br/>Public OAuth Client
    participant A as Okta /authorize
    participant T as Okta /token

    Note over S: Auth JS creates and tracks<br/>state + nonce + PKCE transaction

    S->>A: Browser GET /authorize<br/>client_id + state + nonce + challenge
    A->>U: Show Okta-hosted sign-in when needed
    U->>A: Authenticate
    A-->>S: Redirect callback<br/>code + state

    Note over S: Auth JS validates callback transaction<br/>and recovers verifier

    S->>T: BROWSER POST /token<br/>code + verifier<br/>no client secret
    T-->>S: ID token + access token

    Note over S: Auth JS manages tokens<br/>in browser environment
~~~

The browser JavaScript environment is the OAuth client.

## 4. Where state, verifier, tokens, and session credentials live

**Question answered:** Which secrets or credentials exist on which side?

~~~mermaid
flowchart TB
    subgraph W["SERVER-SIDE WEB APPLICATION"]
        WSERVER["Backend server"]
        WTX["Pending OAuth transaction<br/>state + nonce + verifier"]
        WTOK["OAuth tokens"]
        WSESSION["Server-side app-session record"]

        WBROWSER["Browser"]
        WCOOKIE["Opaque HttpOnly<br/>application-session cookie"]

        WSERVER --> WTX
        WSERVER --> WTOK
        WSERVER --> WSESSION
        WBROWSER --> WCOOKIE
    end

    subgraph S["BROWSER SPA"]
        SBROWSER["Browser JavaScript environment"]
        STX["OAuth transaction state<br/>including PKCE state"]
        STOK["OAuth tokens<br/>managed by Auth JS"]
        SSTORAGE["Browser storage<br/>sessionStorage in our lab"]

        SBROWSER --> STX
        SBROWSER --> STOK
        STX --> SSTORAGE
        STOK --> SSTORAGE
    end
~~~

Our lab intentionally makes the storage difference visible.

## 5. What Browser DevTools can and cannot show

**Question answered:** Why does troubleshooting evidence differ between the two architectures?

~~~mermaid
flowchart LR
    subgraph WEB["WEB APPLICATION"]
        WNET["Browser Network"]
        WSEE["CAN SEE<br/>redirects<br/>callback<br/>application cookie"]
        WHIDE["CANNOT DIRECTLY SEE<br/>backend /token request<br/>client secret<br/>backend token response"]
        WNET --> WSEE
        WNET --> WHIDE
    end

    subgraph SPA["SPA"]
        SNET["Browser Network"]
        SSEE["CAN SEE<br/>redirects<br/>callback<br/>browser /token request<br/>browser storage activity"]
        SNET --> SSEE
    end
~~~

For the Web Application, backend logs are part of the evidence.

## 6. OAuth success vs local application-session failure

**Question answered:** How can Okta login succeed while the Web Application still looks signed out?

~~~mermaid
flowchart TB
    AUTH["Okta authentication succeeds"]
    CALLBACK["Callback receives code + state"]
    TOKEN["Backend /token succeeds"]
    VALID["ID token validates"]
    SESSION{"Local application session<br/>created successfully?"}
    YES["User is signed in to application"]
    NO["Application still appears signed out<br/><br/>OAuth succeeded<br/>local session failed"]

    AUTH --> CALLBACK --> TOKEN --> VALID --> SESSION
    SESSION -->|Yes| YES
    SESSION -->|No| NO
~~~

Do not diagnose the final state as an Okta authentication failure without tracing the earlier steps.

## 7. Simple SPA vs BFF

**Question answered:** What changes when a backend is inserted to keep OAuth tokens away from browser JavaScript?

~~~mermaid
flowchart LR
    subgraph SIMPLE["SIMPLE SPA"]
        S["Browser SPA<br/>holds OAuth tokens"]
        API1["Resource APIs"]
        S -->|"Bearer access token"| API1
    end

    subgraph BFFMODEL["BFF MODEL"]
        B["Browser<br/>holds app-session cookie"]
        F["Backend for Frontend<br/>holds OAuth tokens"]
        API2["Downstream APIs"]

        B -->|"HttpOnly session cookie"| F
        F -->|"Bearer access token"| API2
    end
~~~

Day 7 recognizes this architecture.

Day 8 introduces an actual protected API.

## 8. Troubleshooting decision

**Question answered:** Where should you investigate first when the screen says the user is signed out?

~~~mermaid
flowchart TB
    START["User appears signed out"]
    AUTH{"Did /authorize and<br/>Okta authentication succeed?"}
    CB{"Did callback reach<br/>the application?"}
    TOKEN{"Did /token succeed?"}
    VALID{"Did token validation succeed?"}
    APP{"Did local application auth state<br/>or session get created?"}
    OAUTH["Investigate OAuth/OIDC step"]
    LOCAL["Investigate application-session<br/>or SPA auth-state code"]
    DONE["Authentication state established"]

    START --> AUTH
    AUTH -->|No| OAUTH
    AUTH -->|Yes| CB
    CB -->|No| OAUTH
    CB -->|Yes| TOKEN
    TOKEN -->|No| OAUTH
    TOKEN -->|Yes| VALID
    VALID -->|No| OAUTH
    VALID -->|Yes| APP
    APP -->|No| LOCAL
    APP -->|Yes| DONE
~~~

The question remains:

> What is the last step I can prove succeeded?
