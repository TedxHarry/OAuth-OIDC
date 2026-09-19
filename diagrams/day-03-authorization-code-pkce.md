# Day 3 Flow Diagrams

These diagrams are part of the Day 3 lesson.

Each diagram answers one specific question.

## 1. Conceptual SPA Authorization Code with PKCE flow

**Question answered:** What happens in a normal SPA flow, and in what order?

The SPA client logic runs inside the browser. It is shown as one participant so the diagram does not imply that the SPA and browser are separate systems.

```mermaid
sequenceDiagram
    autonumber
    actor U as Employee
    participant SPA as SPA Client Logic<br/>(inside browser)
    participant A as Okta /authorize
    participant T as Okta /token

    Note over SPA: STEP 1<br/>Create state, nonce, code_verifier
    Note over SPA: STEP 2<br/>Derive code_challenge

    SPA->>A: STEP 3 - GET /authorize<br/>client_id<br/>redirect_uri<br/>scope<br/>state<br/>nonce<br/>code_challenge<br/>code_challenge_method=S256

    A->>U: STEP 4 - Show sign-in when required
    U->>A: STEP 5 - Complete authentication

    A-->>SPA: STEP 6 - Browser redirect to callback<br/>code + state

    Note over SPA: STEP 7 - CLIENT CHECK<br/>returned state must equal expected state

    SPA->>T: STEP 8 - POST /token<br/>code<br/>client_id<br/>redirect_uri<br/>code_verifier

    Note over T: STEP 9 - OKTA CHECK<br/>derive challenge from verifier<br/>compare with stored challenge

    T-->>SPA: STEP 10 - Token response<br/>access_token + id_token
```

### Read it as two phases

```text
PHASE 1 - Browser authorization

SPA client
   |
   | GET /authorize with challenge
   v
Okta
   |
   | user authentication
   v
SPA callback receives code + state


PHASE 2 - Code redemption

SPA client
   |
   | POST /token with code + verifier
   v
Okta
   |
   | PKCE verification
   v
Tokens
```

PKCE connects Phase 1 and Phase 2.

## 2. Day 3 lab flow

**Question answered:** How does our training lab reproduce the same flow manually?

In the lab, Python and Postman temporarily perform pieces that a real SPA library would normally perform automatically.

**Important:** all of these tools together represent one logical training client. They are separated only so the learner can inspect each protocol step.

```mermaid
sequenceDiagram
    autonumber
    actor U as Learner
    participant P as Python Preparation Script
    participant B as Browser
    participant A as Okta /authorize
    participant C as Python Callback Server
    participant PM as Postman
    participant T as Okta /token

    U->>P: Run preparation script
    P-->>U: state + nonce + verifier + challenge + authorize URL

    U->>B: Paste authorization URL
    B->>A: GET /authorize with challenge and transaction values

    A->>U: Show sign-in when required
    U->>A: Complete authentication

    A-->>B: 302 redirect with code + state
    B->>C: GET /callback?code=...&state=...

    C-->>U: Display returned code and state
    Note over U: Compare returned state<br/>with generated state

    U->>PM: Build token request with<br/>code + original verifier
    PM->>T: POST /token
    T-->>PM: access_token + id_token
```

### What each lab tool represents

| Lab tool | What it is doing |
|---|---|
| Python preparation script | Generates values a real SPA library would generate |
| Browser | Carries the front-channel authorization request and redirect |
| Python callback server | Receives the browser callback for training |
| Postman | Manually performs the token request that client code would normally perform |
| Okta | Authorization server and OpenID Provider |

## 3. How the PKCE values are created

**Question answered:** What is the exact relationship between the verifier and challenge?

```mermaid
flowchart LR
    V["1. code_verifier<br/>Random secret for one transaction"]
    H["2. SHA-256<br/>Hash the verifier"]
    E["3. Base64URL<br/>Encode the hash without padding"]
    C["4. code_challenge<br/>Derived value"]

    V --> H --> E --> C
```

### Where they go

```text
code_verifier
-> keep with the client
-> send later to /token

code_challenge
-> safe derived value
-> send first to /authorize
```

## 4. Which values travel at each stage

**Question answered:** What is sent to /authorize, returned to the callback, and sent to /token?

```mermaid
flowchart TB
    START["CLIENT CREATES<br/>state<br/>nonce<br/>code_verifier<br/>code_challenge"]

    AUTH["STEP A - /authorize<br/><br/>SEND:<br/>client_id<br/>response_type=code<br/>redirect_uri<br/>scope<br/>state<br/>nonce<br/>code_challenge<br/>code_challenge_method=S256"]

    CALLBACK["STEP B - callback<br/><br/>RECEIVE:<br/>authorization code<br/>returned state"]

    CHECK["STEP C - client validation<br/><br/>CHECK:<br/>returned state == expected state"]

    TOKEN["STEP D - /token<br/><br/>SEND:<br/>grant_type=authorization_code<br/>client_id<br/>redirect_uri<br/>authorization code<br/>code_verifier"]

    RESULT["STEP E - token response<br/><br/>RECEIVE:<br/>access_token<br/>id_token"]

    START --> AUTH --> CALLBACK --> CHECK --> TOKEN --> RESULT
```

The original verifier does **not** go to `/authorize`.

The challenge does **not** replace the verifier at `/token`.

## 5. What exactly Okta checks for PKCE

**Question answered:** What comparison causes PKCE to pass or fail?

```mermaid
flowchart LR
    STORED["Stored from /authorize<br/><br/>code_challenge"]
    RECEIVED["Received at /token<br/><br/>code_verifier"]
    DERIVE["Okta derives<br/><br/>Base64URL(SHA256(code_verifier))"]
    COMPARE{"Does calculated challenge<br/>equal stored challenge?"}
    PASS["YES<br/><br/>PKCE check passes"]
    FAIL["NO<br/><br/>Token request rejected"]

    RECEIVED --> DERIVE --> COMPARE
    STORED --> COMPARE
    COMPARE -->|Match| PASS
    COMPARE -->|No match| FAIL
```

## 6. Why a stolen authorization code is not enough

**Question answered:** What additional protection does PKCE give the code?

```mermaid
flowchart TB
    CODE["Attacker obtains<br/>authorization code"]
    Q{"Does attacker also possess<br/>the original code_verifier?"}
    NO["No verifier<br/>or wrong verifier"]
    FAIL["Calculated challenge differs<br/>from stored challenge<br/><br/>TOKEN REQUEST REJECTED"]
    YES["Original verifier is also compromised"]
    CONTINUE["PKCE proof can pass<br/>subject to all other token checks"]

    CODE --> Q
    Q -->|No| NO --> FAIL
    Q -->|Yes| YES --> CONTINUE
```

PKCE does not make the authorization code unimportant.

It makes possession of the code alone insufficient for a valid PKCE redemption.

## 7. State, nonce, and PKCE protect different things

**Question answered:** Which control is responsible for which validation?

```mermaid
flowchart TB
    S["state<br/><br/>Protects and correlates<br/>the browser authorization response"]
    N["nonce<br/><br/>Binds the OIDC ID token<br/>to the authentication request"]
    P["PKCE<br/><br/>Binds code redemption<br/>to the verifier created before authorization"]

    SC["WHO CHECKS IT?<br/>Client application<br/>after callback"]
    NC["WHO CHECKS IT?<br/>OIDC client<br/>during ID token validation"]
    PC["WHO CHECKS IT?<br/>Okta<br/>during /token processing"]

    S --> SC
    N --> NC
    P --> PC
```

### Quick comparison

| Control | Created by | Sent first | Checked by | Protects |
|---|---|---|---|---|
| `state` | Client | `/authorize` | Client | Browser authorization response |
| `nonce` | Client | `/authorize` | OIDC client | ID token binding |
| PKCE verifier/challenge | Client | Challenge at `/authorize` | Okta at `/token` | Authorization-code redemption |

## 8. Public SPA vs confidential web application

**Question answered:** How are PKCE and client authentication different?

```mermaid
flowchart TB
    SPA["PUBLIC SPA<br/>Runs in user's browser"]
    WEB["CONFIDENTIAL WEB APP<br/>Runs on controlled backend"]

    SPA --> SPK["Uses Authorization Code + PKCE"]
    SPA --> NONE["Does not rely on a protected client secret"]

    WEB --> WPK["Can use Authorization Code + PKCE"]
    WEB --> AUTH["Can also authenticate the client<br/>using a secret or private key"]

    SPK --> PKCERULE["PKCE<br/>Protects code redemption"]
    WPK --> PKCERULE

    AUTH --> CARULE["Client authentication<br/>Proves registered client identity"]
```

PKCE and client authentication can both exist in a confidential-client flow.

They are not substitutes.
