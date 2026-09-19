# Day 3 Flow Diagrams

These diagrams are part of the Day 3 lesson.

Each diagram answers one specific question.

## 1. Complete Authorization Code with PKCE transaction

**Question answered:** Who sends what, to whom, and in what order?

```mermaid
sequenceDiagram
    autonumber
    actor U as Employee
    participant C as Public Client
    participant B as Browser
    participant A as Okta /authorize
    participant CB as App Callback
    participant T as Okta /token

    Note over C: Create state
    Note over C: Create nonce
    Note over C: Create code_verifier
    Note over C: Derive code_challenge

    C->>B: Open authorization URL

    B->>A: GET /authorize
    Note right of B: Sends client_id<br/>redirect_uri<br/>scope<br/>state<br/>nonce<br/>code_challenge<br/>S256

    A->>U: Request sign-in when required
    U->>A: Complete authentication

    A-->>B: HTTP 302 redirect
    Note right of A: Location contains<br/>code + state

    B->>CB: GET /callback?code=...&state=...

    Note over C,CB: CLIENT CHECK<br/>Returned state must equal expected state

    C->>T: POST /token
    Note right of C: Sends code<br/>client_id<br/>redirect_uri<br/>code_verifier

    Note over T: OKTA PKCE CHECK<br/>SHA256 + Base64URL(verifier)<br/>must match stored challenge

    T-->>C: Access token + ID token
```

### How to read it

There are two major phases:

```text
PHASE 1
Browser authorization
/authorize
        |
        v
authorization code


PHASE 2
Code redemption
/token
        |
        v
tokens
```

PKCE connects the two phases.

## 2. How the PKCE values are created

**Question answered:** What is the relationship between the verifier and challenge?

```mermaid
flowchart LR
    V["1. code_verifier<br/>Random secret for this transaction"]
    H["2. SHA-256<br/>Hash the verifier"]
    E["3. Base64URL<br/>Encode without padding"]
    C["4. code_challenge<br/>Derived public value"]

    V --> H --> E --> C
```

Important:

```text
code_verifier
-> keep for /token

code_challenge
-> send to /authorize
```

## 3. Where each important value travels

**Question answered:** Which values go to /authorize, callback, and /token?

```mermaid
flowchart TB
    START["Client creates<br/>state + nonce + verifier + challenge"]

    AUTH["/authorize request<br/><br/>client_id<br/>response_type=code<br/>redirect_uri<br/>scope<br/>state<br/>nonce<br/>code_challenge<br/>code_challenge_method=S256"]

    CALLBACK["Callback response<br/><br/>code<br/>state"]

    CHECK["Client-side check<br/><br/>returned state == expected state"]

    TOKEN["/token request<br/><br/>grant_type=authorization_code<br/>client_id<br/>redirect_uri<br/>code<br/>code_verifier"]

    RESULT["Token response<br/><br/>access_token<br/>id_token"]

    START --> AUTH --> CALLBACK --> CHECK --> TOKEN --> RESULT
```

The verifier skips the browser authorization request.

It appears only when redeeming the code.

## 4. PKCE verification inside Okta

**Question answered:** What exactly does Okta compare?

```mermaid
flowchart LR
    SV["Stored from /authorize<br/>code_challenge"]
    RV["Received at /token<br/>code_verifier"]
    HASH["Okta calculates<br/>Base64URL(SHA256(code_verifier))"]
    CMP{"Calculated challenge<br/>matches stored challenge?"}
    YES["YES<br/>PKCE check passes"]
    NO["NO<br/>Token request rejected"]

    RV --> HASH --> CMP
    SV --> CMP
    CMP -->|Match| YES
    CMP -->|No match| NO
```

## 5. Why a stolen authorization code is not enough

**Question answered:** What protection does PKCE add?

```mermaid
flowchart TB
    CODE["Attacker obtains<br/>authorization code"]
    Q{"Does attacker also have<br/>the original code_verifier?"}
    WRONG["Wrong or missing verifier"]
    FAIL["Derived challenge does not match<br/>Token request rejected"]
    RIGHT["Original verifier"]
    CHECK["PKCE check can pass<br/>subject to all other token checks"]

    CODE --> Q
    Q -->|No| WRONG --> FAIL
    Q -->|Yes| RIGHT --> CHECK
```

PKCE is not saying the code is harmless.

It adds another required proof for redemption.

## 6. State, nonce, and PKCE are different controls

**Question answered:** Which control protects which part of the flow?

```mermaid
flowchart LR
    S["state<br/><br/>Protects and correlates<br/>browser authorization response"]
    N["nonce<br/><br/>Binds OIDC ID token<br/>to authentication request"]
    P["PKCE<br/><br/>Binds authorization-code redemption<br/>to the verifier created by client"]

    S --> SC["Checked by client<br/>after callback"]
    N --> NC["Checked by OIDC client<br/>when validating ID token"]
    P --> PC["Checked by Okta<br/>during /token request"]
```

Do not substitute one for another.

## 7. Public SPA vs confidential web application

**Question answered:** How do PKCE and client authentication differ?

```mermaid
flowchart TB
    SPA["Public SPA<br/>Runs in browser"]
    WEB["Confidential web app<br/>Runs on controlled backend"]

    SPA --> SPK["Authorization Code + PKCE"]
    SPA --> NONE["No protected client secret"]

    WEB --> WPK["Authorization Code + PKCE"]
    WEB --> AUTH["Can also authenticate client<br/>with secret or private key"]

    SPK --> RULE["PKCE protects code redemption"]
    WPK --> RULE
    AUTH --> CR["Client authentication proves<br/>registered client identity"]
```

Both controls can exist in the same confidential-client flow.

They solve different problems.
