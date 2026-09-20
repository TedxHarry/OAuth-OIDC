# Day 13 Troubleshooting Diagrams

These diagrams support the Day 13 lesson.

Each diagram answers one troubleshooting question.

## 1. Find the last confirmed successful step

**Question answered:** Where should investigation begin?

~~~mermaid
flowchart TB
    START["User reports: Login failed"]

    A{"Browser left application?"}
    B{"Browser reached Okta /authorize?"}
    C{"User authentication/app access succeeded?"}
    D{"Callback reached application?"}
    E{"State and pending transaction valid?"}
    F{"/token succeeded?"}
    G{"OIDC response validated?"}
    H{"Local application auth state created?"}
    I["Signed-in application"]

    APP["Application/JavaScript/configuration"]
    AUTHREQ["OAuth request/client/redirect URI"]
    POLICY["Assignment / authentication policy / user state"]
    CALLBACK["Callback routing / browser return"]
    TX["State / transaction storage / cookies"]
    TOKEN["Token exchange / PKCE / client authentication"]
    OIDC["Nonce / issuer / token validation"]
    SESSION["Local session / SPA auth state / cookies"]

    START --> A
    A -->|No| APP
    A -->|Yes| B
    B -->|No| AUTHREQ
    B -->|Yes| C
    C -->|No| POLICY
    C -->|Yes| D
    D -->|No| CALLBACK
    D -->|Yes| E
    E -->|No| TX
    E -->|Yes| F
    F -->|No| TOKEN
    F -->|Yes| G
    G -->|No| OIDC
    G -->|Yes| H
    H -->|No| SESSION
    H -->|Yes| I
~~~

Do not troubleshoot a later layer until the earlier checkpoints are proven.

## 2. Redirect URI mismatch

**Question answered:** What evidence proves a redirect mismatch?

~~~mermaid
sequenceDiagram
    participant APP as Application
    participant B as Browser
    participant O as Okta

    APP-->>B: Redirect to /authorize<br/>redirect_uri = URI-A
    B->>O: GET /authorize

    Note over O: Compare URI-A<br/>with registered redirect URIs

    O-->>B: Authorization request rejected

    Note over APP: Callback never receives<br/>authorization code
~~~

Compare the actual request value with the registered value exactly.

## 3. State failure vs nonce failure

**Question answered:** At which point does each failure occur?

~~~mermaid
flowchart TB
    CALLBACK["Callback<br/>code + state"]
    STATE{"state matches<br/>pending transaction?"}
    TOKEN["POST /token"]
    ID["ID token returned"]
    NONCE{"nonce matches<br/>expected OIDC request?"}
    OK["Create application auth state"]

    STATEFAIL["STOP<br/>transaction correlation failed"]
    NONCEFAIL["STOP<br/>OIDC response binding failed"]

    CALLBACK --> STATE
    STATE -->|No| STATEFAIL
    STATE -->|Yes| TOKEN --> ID --> NONCE
    NONCE -->|No| NONCEFAIL
    NONCE -->|Yes| OK
~~~

A nonce failure proves the flow made it further than a state failure.

## 4. Missing pending transaction

**Question answered:** Why can a valid callback still be rejected by the application?

~~~mermaid
sequenceDiagram
    participant APP as Web Application
    participant B as Browser
    participant O as Okta

    APP->>APP: Store state, nonce, verifier
    APP-->>B: Redirect to Okta

    Note over APP: Server restarts or<br/>transaction store is lost

    B->>O: Authenticate
    O-->>B: callback?code=...&state=...
    B->>APP: GET /callback

    Note over APP: Callback exists<br/>but expected transaction does not

    APP-->>B: Reject callback
~~~

This is not proof that Okta authentication failed.

## 5. Unexpected MFA troubleshooting

**Question answered:** Which policy layers should be checked first?

~~~mermaid
flowchart TB
    USER["User attempts app sign-in"]
    GSP["Global Session Policy<br/>session establishment / org-level requirements"]
    APPPOL["App Sign-In / Authentication Policy<br/>app-specific assurance / reauthentication"]
    AUTHN["Authenticator enrollment and<br/>current session context"]
    PROMPT["Observed authentication prompt"]

    USER --> GSP --> APPPOL --> AUTHN --> PROMPT

    ASP["Authorization Server Access Policy<br/>token issuance / scopes / grant / lifetime"]

    ASP -. "Different control plane" .-> PROMPT
~~~

Do not start with Custom Authorization Server access policy for an MFA prompt.

## 6. Local logout followed by SSO

**Question answered:** Why can logout look unsuccessful even when local logout worked?

~~~mermaid
sequenceDiagram
    participant B as Browser
    participant APP as Application
    participant O as Okta

    B->>APP: Local logout
    APP-->>B: Delete local session

    Note over O: Okta browser session remains

    B->>APP: Open protected route
    APP-->>B: Redirect to /authorize
    B->>O: Authorization request
    O-->>B: SSO using existing Okta session
    B->>APP: Callback
    APP-->>B: Create new local session
~~~

Name the session you intended to end.

## 7. Login loop analysis

**Question answered:** How do you turn a loop into checkpoints?

~~~mermaid
flowchart LR
    APP["App says unauthenticated"]
    OKTA["Okta authorization"]
    CALLBACK["Callback"]
    TOKEN["Token/OIDC success"]
    LOCAL["Local auth state missing"]

    APP --> OKTA --> CALLBACK --> TOKEN --> LOCAL --> APP
~~~

The loop can exist even when Okta authentication and token issuance succeed.

## 8. Browser cookie vs server-session failure

**Question answered:** Is the browser losing the cookie, or is the server losing the session?

~~~mermaid
flowchart TB
    SET["Application sends Set-Cookie"]
    STORE{"Browser stores cookie?"}
    SEND{"Browser sends cookie<br/>on next request?"}
    SERVER{"Server recognizes<br/>session ID?"}

    BROWSERFAIL["Browser cookie problem<br/>domain/path/Secure/SameSite/privacy"]
    SERVERFAIL["Server session problem<br/>expired/lost/store/node mismatch"]
    OK["Local application session works"]

    SET --> STORE
    STORE -->|No| BROWSERFAIL
    STORE -->|Yes| SEND
    SEND -->|No| BROWSERFAIL
    SEND -->|Yes| SERVER
    SERVER -->|No| SERVERFAIL
    SERVER -->|Yes| OK
~~~

Do not change Okta policy when the local session store is the failed layer.

## 9. Postman works, browser fails

**Question answered:** What new layers exist only in the browser?

~~~mermaid
flowchart TB
    REQUEST["Same intended operation"]

    POSTMAN["Postman / curl"]
    BROWSER["Browser JavaScript"]

    HTTP["HTTP server behavior"]
    EXTRA["Browser-only layers<br/>CORS<br/>origin<br/>preflight<br/>cookie/privacy<br/>storage<br/>JavaScript<br/>mixed content"]

    REQUEST --> POSTMAN --> HTTP
    REQUEST --> BROWSER --> EXTRA --> HTTP
~~~

Postman success narrows the search but does not prove the browser path.

## 10. CORS preflight

**Question answered:** Why might the API never receive the expected GET?

~~~mermaid
sequenceDiagram
    participant B as Browser SPA
    participant API as Cross-Origin API

    B->>API: OPTIONS /data<br/>Origin: SPA origin<br/>Request-Method: GET<br/>Request-Headers: Authorization

    alt CORS permits origin/method/header
        API-->>B: 204 + Access-Control-Allow-*
        B->>API: GET /data<br/>Authorization: Bearer ...
        API-->>B: 200
    else CORS response missing/insufficient
        API-->>B: Preflight response
        Note over B: Browser blocks actual GET
    end
~~~

Check whether the protected request was ever sent.

## 11. Your API CORS vs Okta Trusted Origins

**Question answered:** Who owns the CORS setting?

~~~mermaid
flowchart TB
    SPA["Browser SPA"]

    YOURAPI["Your Employee API<br/>different origin"]
    OKTACOOKIE["Okta API call<br/>using Okta session cookie"]
    OKTABEARER["Supported Okta API call<br/>using OAuth bearer token"]

    APICORS["Configure CORS on<br/>YOUR API"]
    TRUST["Okta Trusted Origin<br/>can be relevant"]
    BEARER["Bearer authorization<br/>does not rely on Okta session cookie"]

    SPA --> YOURAPI --> APICORS
    SPA --> OKTACOOKIE --> TRUST
    SPA --> OKTABEARER --> BEARER
~~~

Do not add an Okta Trusted Origin to fix CORS on your own API.

## 12. Dev works, prod fails

**Question answered:** How should two environments be compared?

~~~mermaid
flowchart LR
    DEV["DEV<br/>issuer<br/>client ID<br/>redirect URI<br/>origin<br/>cookie config<br/>policy<br/>assignment"]

    COMPARE["Compare every trust/config boundary"]

    PROD["PROD<br/>issuer<br/>client ID<br/>redirect URI<br/>origin<br/>cookie config<br/>policy<br/>assignment"]

    DEV --> COMPARE --> PROD
~~~

Treat environment differences as evidence, not assumptions.

## 13. System Log correlation

**Question answered:** How does Okta evidence fit with browser/application evidence?

~~~mermaid
flowchart TB
    INCIDENT["One sign-in incident"]

    BROWSER["Browser evidence<br/>redirects / callback / storage / cookies"]
    APP["Application evidence<br/>transaction / token exchange / local session"]
    OKTA["Okta System Log<br/>authentication / app SSO / policy / session"]

    CORR["Correlate by<br/>time<br/>user<br/>app/client<br/>transaction.id<br/>externalSessionId<br/>rootSessionId"]

    INCIDENT --> BROWSER
    INCIDENT --> APP
    INCIDENT --> OKTA

    BROWSER --> CORR
    APP --> CORR
    OKTA --> CORR
~~~

No single source proves every layer.

## 14. Evidence-driven incident note

**Question answered:** What should the final diagnosis look like?

~~~mermaid
flowchart TB
    SYM["Observed symptom"]
    LAST["Last confirmed successful step"]
    FIRST["First failed step"]
    EVID["Evidence"]
    ROOT["Root cause"]
    CHANGE["One relevant change"]
    PROOF["Repeat transaction and prove result"]

    SYM --> LAST --> FIRST --> EVID --> ROOT --> CHANGE --> PROOF
~~~

A fix without proof is not the end of the troubleshooting exercise.
