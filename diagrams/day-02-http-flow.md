# Day 2 Flow Diagrams

These diagrams support the Day 2 lesson.

## 1. HTTP request and response

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    C->>S: HTTP request
    S-->>C: HTTP response
```

The client can be a browser, Postman, Python application, backend service, or another application component.

## 2. Redirect

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Server
    participant C as Callback endpoint

    B->>S: GET /start
    S-->>B: 302 Location: /callback?code=demo-code&state=demo-state
    B->>C: GET /callback?code=demo-code&state=demo-state
    C-->>B: 200 OK
```

The browser follows the location supplied by the server.

## 3. Front-channel communication

```mermaid
sequenceDiagram
    participant A as Application
    participant B as Browser
    participant O as Authorization Server

    A-->>B: Redirect instruction
    B->>O: Browser request
    O-->>B: Redirect instruction
    B->>A: Callback request
```

The browser carries the transaction between the application and authorization server.

## 4. Back-channel communication

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as Application Backend
    participant O as Authorization Server

    B->>A: User request
    A->>O: Direct HTTPS request
    O-->>A: Direct HTTPS response
    A-->>B: Application response
```

The browser does not carry the direct backend-to-server request.

## 5. Cookie behavior

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Web Server

    B->>S: GET /set-cookie
    S-->>B: Set-Cookie: demo_session=abc123
    B->>S: GET /show-cookie with Cookie header
    S-->>B: Cookie value received
```

The browser can return cookies automatically for the appropriate site.

## 6. Bearer token API request

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API

    C->>A: GET /protected without token
    A-->>C: 401

    C->>A: GET /protected with Authorization: Bearer demo-token
    A-->>C: 200 OK
```

The application deliberately places the bearer token in the Authorization header.
