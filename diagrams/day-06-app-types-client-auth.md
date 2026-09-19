# Day 6 Flow Diagrams

These diagrams support the Day 6 lesson.

## 1. Choose app type from runtime architecture

**Question answered:** Which application component is actually the OAuth client?

~~~mermaid
flowchart TB
    Q["START<br/>Which component requests authorization or tokens?"]
    BROWSER{"Does the client run in a browser<br/>and lack secure credential storage?"}
    BACKEND{"Does the client run on a controlled backend<br/>and protect credentials?"}
    NATIVE{"Is it installed on a user-controlled device?"}
    SERVICE{"Is it a non-user service<br/>requesting tokens?"}

    SPA["SPA<br/>PUBLIC CLIENT"]
    WEB["Web Application<br/>CONFIDENTIAL CLIENT"]
    NAT["Native Application<br/>PUBLIC CLIENT"]
    SVC["Service / API Service pattern<br/>CONFIDENTIAL SERVICE CLIENT"]
    REVIEW["Review the actual architecture<br/>before choosing"]

    Q --> BROWSER
    BROWSER -->|Yes| SPA
    BROWSER -->|No| BACKEND
    BACKEND -->|Yes| WEB
    BACKEND -->|No| NATIVE
    NATIVE -->|Yes| NAT
    NATIVE -->|No| SERVICE
    SERVICE -->|Yes| SVC
    SERVICE -->|No| REVIEW
~~~

The runtime component decides the classification.

## 2. One project can contain several OAuth roles

**Question answered:** Why can one business application contain several OAuth roles?

~~~mermaid
flowchart LR
    USER["Employee Browser"]
    SPA["React SPA<br/>OAuth Client<br/>Public"]
    API["Employee API<br/>Resource Server"]
    JOB["Nightly Python Job<br/>OAuth Client<br/>Confidential"]
    OKTA["Okta<br/>Authorization Server"]

    USER --> SPA
    SPA -->|Authorization request| OKTA
    OKTA -->|Tokens| SPA
    SPA -->|Bearer access token| API

    JOB -->|Token request| OKTA
    OKTA -->|Access token| JOB
    JOB -->|Bearer access token| API
~~~

The Employee API is a resource server here, not automatically an OAuth client.

## 3. Public SPA token request

**Question answered:** What is present when the client has no protected secret?

~~~mermaid
flowchart TB
    SPA["SPA Public Client"]
    REQ["POST /token<br/><br/>client_id<br/>authorization code<br/>redirect_uri<br/>code_verifier"]
    OKTA["Okta Token Endpoint"]
    CHECK["Check code transaction<br/>and PKCE verifier"]
    RESULT["Token response"]

    SPA --> REQ --> OKTA --> CHECK --> RESULT
~~~

Client authentication method:

~~~text
none
~~~

## 4. Confidential Web Application token request

**Question answered:** Which two independent proofs can be checked?

~~~mermaid
sequenceDiagram
    autonumber
    participant W as Web Application Backend
    participant T as Okta /token

    Note over W: Stores client secret<br/>on controlled backend
    Note over W: Retains PKCE code_verifier<br/>for this transaction

    W->>T: POST /token<br/>Basic client authentication<br/>code + redirect_uri + code_verifier

    Note over T: CHECK A<br/>Is client authentication valid?

    Note over T: CHECK B<br/>Does verifier match PKCE challenge?

    T-->>W: Token response only if<br/>required checks pass
~~~

~~~text
Client secret
-> client identity proof

PKCE verifier
-> transaction-specific code-redemption proof
~~~

## 5. client_secret_basic vs client_secret_post

**Question answered:** Where is the shared client secret carried?

~~~mermaid
flowchart LR
    BASIC["client_secret_basic"]
    BH["HTTP Authorization header<br/><br/>Basic Base64(client_id:client_secret)"]

    POST["client_secret_post"]
    PB["POST form body<br/><br/>client_id=...<br/>client_secret=..."]

    BASIC --> BH
    POST --> PB
~~~

Use the method configured for the client.

## 6. Shared secret vs private_key_jwt

**Question answered:** What is the high-level difference between shared-secret and asymmetric client authentication?

~~~mermaid
flowchart TB
    SHARED["SHARED SECRET"]
    BOTH["Client knows secret<br/>Okta knows secret"]

    PKJ["PRIVATE_KEY_JWT"]
    PRIVATE["Client keeps private key"]
    ASSERT["Client signs JWT assertion"]
    PUBLIC["Okta has public key"]
    VERIFY["Okta verifies assertion"]

    SHARED --> BOTH

    PKJ --> PRIVATE --> ASSERT --> VERIFY
    PKJ --> PUBLIC --> VERIFY
~~~

Day 12 implements private_key_jwt.

## 7. PKCE and client authentication are separate checks

**Question answered:** Why can a confidential Web Application use both?

~~~mermaid
flowchart TB
    TOKEN["POST /token"]
    CA{"CHECK 1<br/>Client authentication valid?"}
    PKCE{"CHECK 2<br/>PKCE verifier valid?"}
    SUCCESS["Continue token processing"]
    FAIL["Reject token request"]

    TOKEN --> CA
    CA -->|No| FAIL
    CA -->|Yes| PKCE
    PKCE -->|No| FAIL
    PKCE -->|Yes| SUCCESS
~~~

One successful check does not cancel a failed required check.

## 8. Resource server vs API Service client

**Question answered:** Why does the word API appear in two different roles?

~~~mermaid
flowchart LR
    CLIENT["OAuth Client<br/>requests token"]
    OKTA["Okta<br/>Authorization Server"]
    RESOURCE["Employee API<br/>RESOURCE SERVER<br/>receives token"]

    CLIENT -->|Token request| OKTA
    OKTA -->|Access token| CLIENT
    CLIENT -->|Bearer access token| RESOURCE

    APISVC["Okta API Service integration<br/>SERVICE CLIENT registration"]

    APISVC -. is a type of client role .-> CLIENT
~~~

A resource server receives tokens.

A service client requests tokens.
