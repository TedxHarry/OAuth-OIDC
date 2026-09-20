# Day 6 Flow Diagrams

These diagrams support the Day 6 lesson.

## 1. Choose app type from runtime architecture

**Question answered:** Which application component is actually the OAuth client?

~~~mermaid
flowchart TB
    Q["START<br/>Which component requests authorization or tokens?"]
    USER{"Is a human user part of<br/>this client's authorization flow?"}
    SERVICE["SERVICE CLIENT<br/>No end user<br/>Confidential machine-to-machine client"]

    BROWSER{"Does the client logic run in the browser<br/>where it cannot protect a credential?"}
    NATIVE{"Does it run on a user-controlled device<br/>without protected client credentials?"}
    BACKEND{"Does it run on a controlled backend<br/>that can protect credentials?"}

    SPA["SPA<br/>PUBLIC CLIENT"]
    NAT["Native Application<br/>PUBLIC CLIENT"]
    WEB["Web Application<br/>CONFIDENTIAL CLIENT"]
    REVIEW["REVIEW ARCHITECTURE<br/>Do not classify from project name alone"]

    Q --> USER
    USER -->|No| SERVICE
    USER -->|Yes| BROWSER
    BROWSER -->|Yes| SPA
    BROWSER -->|No| NATIVE
    NATIVE -->|Yes| NAT
    NATIVE -->|No| BACKEND
    BACKEND -->|Yes| WEB
    BACKEND -->|No| REVIEW
~~~

The runtime component decides the classification.

## 2. One project can contain several OAuth roles

**Question answered:** Why can one business application contain several OAuth roles?

~~~mermaid
flowchart LR
    USER["Employee Browser"]
    SPA["React SPA<br/>OAuth Client<br/>Public"]
    JOB["Nightly Python Job<br/>OAuth Client<br/>Confidential"]
    AS["Authorization Server for Employee API<br/><br/>Custom AS covered on Day 9"]
    API["Employee API<br/>RESOURCE SERVER"]

    USER --> SPA

    SPA -->|Authorization request| AS
    AS -->|Access token intended for Employee API| SPA
    SPA -->|Bearer access token| API

    JOB -->|Machine-to-machine token request| AS
    AS -->|Access token intended for Employee API| JOB
    JOB -->|Bearer access token| API
~~~

The Employee API is a resource server here, not automatically an OAuth client.

The authorization server shown here is **not** the Org Authorization Server used in the earlier SSO labs. A custom API needs an access token intended for that API. We configure that boundary on Day 9.

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

## 8. Resource server vs API Services client

**Question answered:** Why does the word API appear in two different roles?

~~~mermaid
flowchart LR
    SVC["API Services app<br/>SERVICE CLIENT<br/>requests tokens"]
    AS["Authorization Server"]
    RESOURCE["Custom API<br/>RESOURCE SERVER<br/>receives access token"]

    SVC -->|Token request| AS
    AS -->|Access token returned to service client| SVC
    SVC -->|Authorization: Bearer access_token| RESOURCE
~~~

A resource server receives tokens.

A service client requests tokens.

The authorization server must issue a token intended for the resource being called.

## 9. Two machine-to-machine service paths

**Question answered:** Why do Day 11 and Day 12 use different authorization-server and client-authentication details?

~~~mermaid
flowchart TB
    OWN["DAY 11<br/>Service calls YOUR API"]
    OWNCLIENT["API Services service client"]
    CUSTOM["Custom Authorization Server"]
    OWNAPI["Your Resource Server"]

    OKTAAPI["DAY 12<br/>Service calls OKTA API"]
    OKTACLIENT["OAuth service app<br/>API Services type"]
    ORG["Org Authorization Server<br/>private_key_jwt<br/>okta.* scopes"]
    MGMT["Okta Management API"]

    OWN --> OWNCLIENT --> CUSTOM --> OWNAPI
    OKTAAPI --> OKTACLIENT --> ORG --> MGMT
~~~

Do not interchange these two token paths.
