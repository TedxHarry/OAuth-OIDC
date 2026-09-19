# Day 4 Flow Diagrams

These diagrams support the Day 4 lesson.

## 1. Three token types and their consumers

**Question answered:** Which component is supposed to use each token?

~~~mermaid
flowchart LR
    O["Authorization Server<br/>Okta"]

    ID["ID TOKEN<br/>Authentication result<br/>for the client"]
    AT["ACCESS TOKEN<br/>Authorization credential<br/>for a resource server"]
    RT["REFRESH TOKEN<br/>Renewal credential<br/>for the authorization server"]

    C["Client Application"]
    API["Resource Server / API"]
    TOKEN["Authorization Server<br/>/token endpoint"]

    O --> ID --> C
    O --> AT --> API
    O --> RT --> TOKEN
~~~

## 2. Token lifecycle

**Question answered:** What happens after tokens are issued?

~~~mermaid
flowchart TB
    AUTH["Authorization succeeds"]
    ISSUE["Authorization server issues tokens"]
    USE["Client uses access token<br/>for intended resource"]
    EXP["Access token reaches expiration"]
    Q{"Valid refresh token<br/>and continued access?"}
    REFRESH["Send refresh token to /token"]
    NEW["Receive new token response"]
    AGAIN["New authorization or sign-in<br/>when required"]

    AUTH --> ISSUE --> USE --> EXP --> Q
    Q -->|Yes| REFRESH --> NEW --> USE
    Q -->|No| AGAIN
~~~

## 3. Refresh token flow for our public SPA

**Question answered:** Where does the refresh token go?

~~~mermaid
sequenceDiagram
    autonumber
    participant C as Public SPA Client
    participant T as Okta /token
    participant R as Intended Resource Server

    Note over C: Client already has<br/>access token + refresh token

    C->>R: API request with access token
    Note over C,R: Later the access token expires

    C->>T: POST /token<br/>grant_type=refresh_token<br/>client_id<br/>refresh_token<br/>scope

    Note over T: Validate refresh token<br/>and refresh request

    T-->>C: New access token<br/>possibly ID token<br/>possibly replacement refresh token

    C->>R: Later use the new access token
~~~

The refresh token goes to the authorization server, not the resource server.

## 4. How a refresh token is obtained

**Question answered:** What must be true before our Authorization Code flow can return a refresh token?

~~~mermaid
flowchart TB
    APP["APP CONFIGURATION<br/>Refresh Token grant enabled"]
    AUTH["AUTHORIZATION REQUEST<br/>scope includes offline_access"]
    CODE["FLOW<br/>Authorization Code + PKCE succeeds"]
    RESULT["TOKEN RESPONSE<br/>can include refresh_token"]

    APP --> RESULT
    AUTH --> RESULT
    CODE --> RESULT
~~~

For Authorization Code flow, offline_access belongs in the authorization request.

## 5. ID token inspection vs validation

**Question answered:** Why is reading a JWT not enough?

~~~mermaid
flowchart LR
    JWT["ID token JWT"]
    DEC["Decode header and payload"]
    READ["Read claims<br/>iss, sub, aud, exp, nonce"]
    TRUST{"Signature and claim<br/>validation completed?"}
    NO["NO<br/>Readable but not yet trusted"]
    YES["YES<br/>Validation completed"]

    JWT --> DEC --> READ --> TRUST
    TRUST -->|No| NO
    TRUST -->|Yes| YES
~~~

Day 4 stops at inspection.

Day 5 teaches validation.

## 6. Org authorization server access-token boundary

**Question answered:** Why are we not using the current access token to protect our own API?

~~~mermaid
flowchart TB
    ORG["Okta Org Authorization Server"]
    OAT["Org-AS Access Token"]
    OKTA["Okta<br/>intended consumer"]
    CUSTOM["Your Custom API"]
    NO["Do not build custom API trust<br/>from Org-AS token contents"]

    ORG --> OAT
    OAT --> OKTA
    OAT -. not intended for this use .-> CUSTOM
    CUSTOM --> NO
~~~

Later:

~~~text
Custom Authorization Server
        |
        v
Access token intended for your API
        |
        v
Your Resource Server
~~~

## 7. Refresh token rotation

**Question answered:** What should the client do if Okta returns a replacement refresh token?

~~~mermaid
flowchart LR
    R1["Current refresh token<br/>R1"]
    CALL["Send R1 to /token"]
    RESP["Receive new token response"]
    Q{"Replacement refresh token<br/>returned?"}
    R2["YES<br/>Securely replace stored token<br/>with returned token R2"]
    KEEP["NO<br/>Continue according to<br/>current valid token state"]

    R1 --> CALL --> RESP --> Q
    Q -->|Yes| R2
    Q -->|No| KEEP
~~~

Do not assume the refresh-token string is permanently fixed.
