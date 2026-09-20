# Day 14 Troubleshooting Diagrams

These diagrams support the Day 14 lesson.

Each diagram answers one troubleshooting question.

## 1. The first question: was a token issued?

**Question answered:** Should you troubleshoot the token endpoint or the resource API?

~~~mermaid
flowchart TB
    START["Access problem"]
    TOKEN{"Did /token return<br/>a usable access token?"}

    PRE["TOKEN-ENDPOINT PATH<br/>client authentication<br/>grant<br/>scope/policy"]
    API{"What did the<br/>resource return?"}

    U401["401<br/>TOKEN TRUST / VALIDATION"]
    U403["403<br/>PERMISSION / AUTHORIZATION"]
    OK["2xx<br/>Move to next application layer"]

    START --> TOKEN
    TOKEN -->|No| PRE
    TOKEN -->|Yes| API
    API -->|401| U401
    API -->|403| U403
    API -->|2xx| OK
~~~

Do not debug API scope enforcement before a usable token exists.

## 2. Token-endpoint failure layers

**Question answered:** What should be checked before the resource server?

~~~mermaid
flowchart TB
    REQ["POST /token"]

    ENDPOINT{"Correct issuer and<br/>token endpoint?"}
    AUTHN{"Client authentication<br/>accepted?"}
    GRANT{"Grant credential<br/>accepted?"}
    SCOPE{"Requested scopes<br/>issuable?"}
    TOKEN["Access token issued"]

    E1["Endpoint/network/configuration"]
    E2["invalid_client / client auth"]
    E3["invalid_grant / grant validation"]
    E4["scope / policy / grant collection"]

    REQ --> ENDPOINT
    ENDPOINT -->|No| E1
    ENDPOINT -->|Yes| AUTHN
    AUTHN -->|No| E2
    AUTHN -->|Yes| GRANT
    GRANT -->|No| E3
    GRANT -->|Yes| SCOPE
    SCOPE -->|No| E4
    SCOPE -->|Yes| TOKEN
~~~

The API is downstream of all four checks.

## 3. invalid_grant depends on the grant type

**Question answered:** Why is the error name not the root cause?

~~~mermaid
flowchart TB
    ERR["invalid_grant"]
    TYPE{"grant_type?"}

    CODE["authorization_code<br/>code expired/reused<br/>PKCE verifier<br/>redirect_uri<br/>wrong transaction"]
    REFRESH["refresh_token<br/>revoked/expired<br/>wrong client<br/>rotation/reuse<br/>wrong issuer"]
    OTHER["Other supported grant<br/>inspect that grant's credential"]

    ERR --> TYPE
    TYPE -->|authorization_code| CODE
    TYPE -->|refresh_token| REFRESH
    TYPE -->|other| OTHER
~~~

Always identify the credential being validated.

## 4. Scope failure at /token vs 403 at API

**Question answered:** Where was permission denied?

~~~mermaid
flowchart LR
    CLIENT["Client"]

    AS["Authorization Server"]
    TOKENFAIL["No token<br/>scope request rejected"]

    TOKEN["Valid access token<br/>scope missing"]
    API["Resource API"]
    FORBID["403 insufficient_scope"]

    CLIENT -->|"request scope"| AS
    AS -->|"scope not issuable"| TOKENFAIL

    CLIENT --> TOKEN --> API
    API -->|"token trusted but endpoint scope absent"| FORBID
~~~

These are different authorization layers.

## 5. Resource-server validation pipeline

**Question answered:** What does a 401 validator actually check?

~~~mermaid
flowchart TB
    REQ["Bearer request"]
    BEARER{"Bearer credential present<br/>and parseable?"}
    ALG{"Allowed alg and kid?"}
    KEY{"kid resolves in<br/>trusted JWKS?"}
    SIG{"Signature valid?"}
    ISS{"iss matches trusted issuer?"}
    AUD{"aud matches API?"}
    TIME{"time claims valid?"}
    CID{"client boundary valid?"}
    TRUST["TOKEN TRUSTED"]
    AUTHZ["Now evaluate scope/permission"]

    FAIL["401 invalid_token"]

    REQ --> BEARER
    BEARER -->|No| FAIL
    BEARER -->|Yes| ALG
    ALG -->|No| FAIL
    ALG -->|Yes| KEY
    KEY -->|No| FAIL
    KEY -->|Yes| SIG
    SIG -->|No| FAIL
    SIG -->|Yes| ISS
    ISS -->|No| FAIL
    ISS -->|Yes| AUD
    AUD -->|No| FAIL
    AUD -->|Yes| TIME
    TIME -->|No| FAIL
    TIME -->|Yes| CID
    CID -->|No| FAIL
    CID -->|Yes| TRUST --> AUTHZ
~~~

Authorization does not begin until the token is trusted.

## 6. 401 vs 403

**Question answered:** Is the credential invalid or merely insufficient?

~~~mermaid
flowchart TB
    REQUEST["API request"]
    TRUST{"Bearer credential<br/>accepted?"}
    PERM{"Required operation<br/>permission present?"}

    R401["401<br/>authentication/trust failure"]
    R403["403<br/>trusted credential<br/>insufficient permission"]
    R200["200 / success"]

    REQUEST --> TRUST
    TRUST -->|No| R401
    TRUST -->|Yes| PERM
    PERM -->|No| R403
    PERM -->|Yes| R200
~~~

A 403 is not a stronger 401.

## 7. Unknown kid investigation

**Question answered:** What should happen when a cached key set does not contain the token kid?

~~~mermaid
flowchart TB
    TOKEN["JWT header kid"]
    CACHE{"kid in cached JWKS?"}
    VALIDATE["Use matching public key"]
    ISSUER["Confirm expected issuer"]
    DISC["Load discovery from trusted issuer"]
    JWKS["Refresh jwks_uri"]
    FOUND{"kid now present?"}
    ROTATE["Likely stale cache / key rotation path"]
    OTHER["Investigate wrong issuer/environment,<br/>fabricated token, wrong JWKS, stale pin"]

    TOKEN --> CACHE
    CACHE -->|Yes| VALIDATE
    CACHE -->|No| ISSUER --> DISC --> JWKS --> FOUND
    FOUND -->|Yes| ROTATE --> VALIDATE
    FOUND -->|No| OTHER
~~~

Never disable signature validation to get past an unknown kid.

## 8. Wrong audience

**Question answered:** Why can a correctly signed token still receive 401?

~~~mermaid
flowchart LR
    AS["Trusted Authorization Server"]
    TOKEN["Signed access token<br/>aud = api://service-A"]
    APIA["Service A<br/>expects api://service-A"]
    APIB["Service B<br/>expects api://service-B"]

    AS --> TOKEN
    TOKEN -->|"aud matches"| APIA
    TOKEN -->|"aud does not match"| APIB

    APIA --> OK["Trusted"]
    APIB --> FAIL["401 audience validation"]
~~~

Signature validity does not make a token universal.

## 9. Refresh troubleshooting

**Question answered:** Which refresh-token state should you inspect?

~~~mermaid
flowchart TB
    REFRESH["Refresh request"]
    CLIENT{"Correct client and issuer?"}
    TOKEN{"Current refresh token?"}
    STATE{"Revoked or expired?"}
    ROTATE{"Rotation/reuse issue?"}
    OK["New token response"]
    FAIL["Refresh fails"]

    REFRESH --> CLIENT
    CLIENT -->|No| FAIL
    CLIENT -->|Yes| TOKEN
    TOKEN -->|No / old token| ROTATE
    TOKEN -->|Yes| STATE
    STATE -->|Yes| FAIL
    STATE -->|No| ROTATE
    ROTATE -->|Reuse detected / wrong current token| FAIL
    ROTATE -->|No issue| OK
~~~

Do not casually replay live rotating refresh tokens.

## 10. Local validation vs live token state

**Question answered:** How can local API 200 coexist with introspection inactive?

~~~mermaid
flowchart LR
    JWT["Already-issued JWT"]

    LOCAL["Local API validator<br/>signature<br/>iss<br/>aud<br/>exp<br/>scope"]
    OKTA["Authorization server<br/>current token state"]

    LRESULT["Can still be 200<br/>while JWT is unexpired"]
    IRESULT["/introspect<br/>active = false"]

    JWT --> LOCAL --> LRESULT
    JWT --> OKTA --> IRESULT
~~~

The two checks answer different questions.

## 11. Client Credentials troubleshooting

**Question answered:** Where can the Day 11 machine flow fail?

~~~mermaid
flowchart TB
    SVC["Reporting Service"]
    AUTHN{"client_secret_basic<br/>accepted?"}
    POLICY{"Client Credentials policy<br/>client + grant + No user + scope?"}
    TOKEN["Machine access token"]
    TRUST{"Employee API trusts<br/>iss/aud/cid/token?"}
    SCOPE{"employee.report.read<br/>present?"}

    E1["No token<br/>client authentication failure"]
    E2["No token<br/>policy/scope failure"]
    E3["401"]
    E4["403"]
    OK["200"]

    SVC --> AUTHN
    AUTHN -->|No| E1
    AUTHN -->|Yes| POLICY
    POLICY -->|No| E2
    POLICY -->|Yes| TOKEN --> TRUST
    TRUST -->|No| E3
    TRUST -->|Yes| SCOPE
    SCOPE -->|No| E4
    SCOPE -->|Yes| OK
~~~

There is no browser or user-policy troubleshooting in this path.

## 12. Okta Management API troubleshooting

**Question answered:** Which Day 12 security layer failed?

~~~mermaid
flowchart TB
    AUTO["Automation"]
    ASSERT{"private_key_jwt<br/>accepted?"}
    GRANT{"Requested okta.* scope<br/>in app grants?"}
    TOKEN["Org-AS access token issued"]
    ADMIN{"Admin role permits<br/>operation?"}
    TARGET{"Resource target permits<br/>object?"}

    E1["Layer 1<br/>client authentication"]
    E2["Layer 2<br/>scope grant"]
    E3["Layer 3<br/>admin authorization"]
    E4["Layer 3<br/>resource authorization"]
    OK["Management API succeeds"]

    AUTO --> ASSERT
    ASSERT -->|No| E1
    ASSERT -->|Yes| GRANT
    GRANT -->|No| E2
    GRANT -->|Yes| TOKEN --> ADMIN
    ADMIN -->|No| E3
    ADMIN -->|Yes| TARGET
    TARGET -->|No| E4
    TARGET -->|Yes| OK
~~~

A successfully issued token proves the first two layers succeeded, not the third.

## 13. Dev works, prod fails

**Question answered:** What should be compared beyond source code?

~~~mermaid
flowchart TB
    DEV["DEV"]
    PROD["PROD"]

    MATRIX["Compare trust configuration"]

    ITEMS["issuer<br/>AS ID<br/>audience<br/>client ID<br/>auth method<br/>secret/key/kid<br/>scope/policy<br/>admin role<br/>resource target<br/>JWKS<br/>expected cid<br/>clock<br/>API base URL"]

    DEV --> MATRIX
    PROD --> MATRIX
    MATRIX --> ITEMS
~~~

OAuth configuration is part of the deployed system.

## 14. Retry or alert?

**Question answered:** Should the application keep retrying?

~~~mermaid
flowchart TB
    FAIL["Failure"]
    TYPE{"Failure type?"}

    CONFIG["Configuration / credential<br/>invalid_client<br/>wrong audience<br/>ungranted scope<br/>missing admin role"]
    TRANSIENT["Potentially transient<br/>network timeout<br/>5xx<br/>rate limit"]

    ALERT["Stop repeated retry<br/>alert / fix configuration"]
    RETRY["Bounded retry<br/>backoff / respect server guidance"]

    FAIL --> TYPE
    TYPE -->|Configuration| CONFIG --> ALERT
    TYPE -->|Transient| TRANSIENT --> RETRY
~~~

Infinite retry does not repair deterministic configuration errors.

## 15. Incident diagnosis record

**Question answered:** What should a complete Day 14 diagnosis contain?

~~~mermaid
flowchart TB
    SYM["Observed symptom"]
    TYPE["Transaction + grant type"]
    LAST["Last successful step"]
    FIRST["First failed step"]
    HTTP["HTTP evidence"]
    SAFE["Safe token/assertion evidence"]
    API["API / System Log evidence"]
    ROOT["Root cause"]
    CHANGE["One change"]
    PROOF["Repeat and prove"]

    SYM --> TYPE --> LAST --> FIRST --> HTTP --> SAFE --> API --> ROOT --> CHANGE --> PROOF
~~~

A fix without a proven failed layer is not a complete diagnosis.
