# Course Diagrams

The diagrams are part of the teaching material. They are not separate presentation graphics.

Use them to answer:

- who talks to whom
- which component owns each step
- what is sent between components
- where trust is established
- where a failure can occur

GitHub renders the Mermaid diagrams directly in Markdown.

## Available

- [Day 1 flows](day-01-flows.md)
- [Day 2 HTTP flows](day-02-http-flow.md)
- [Day 3 Authorization Code with PKCE](day-03-authorization-code-pkce.md)
- [Day 4 token lifecycle](day-04-token-lifecycle.md)
- [Day 5 JWT validation](day-05-jwt-validation.md)
- [Day 6 app types and client authentication](day-06-app-types-client-auth.md)
- [Day 7 server-side Web App vs browser SPA](day-07-web-app-vs-spa.md)
- [Day 8 protected API](day-08-protect-api.md)
- [Day 9 authorization-server design](day-09-authorization-design.md)
- [Day 10 session and token lifecycle](day-10-session-token-lifecycle.md)
- [Day 11 Client Credentials and machine-to-machine](day-11-client-credentials.md)
- [Day 12 Okta Management API automation](day-12-okta-api-automation.md)
- [Day 13 browser and authentication troubleshooting](day-13-browser-auth-troubleshooting.md)
- [Day 14 token, API, refresh, and automation troubleshooting](day-14-token-api-automation-troubleshooting.md)

## Diagram plan

| Day | Main diagrams |
|---|---|
| 1 | Authentication vs API authorization, token consumers, public vs confidential client, user path, scheduled service path |
| 2 | Browser redirects, front channel vs back channel, request and response path |
| 3 | Authorization Code + PKCE sequence, state, nonce, verifier and challenge |
| 4 | ID/access/refresh token lifecycle, refresh flow |
| 5 | Discovery, JWKS, JWT validation, validation vs authorization |
| 6 | Okta app configuration relationships, client authentication methods |
| 7 | Server-side web app vs SPA flow |
| 8 | Protected API request, 401 vs 403 decision path |
| 9 | Org vs Custom Authorization Server, requested scope to policy to token to API |
| 10 | Okta session, app session, tokens, logout, revocation, introspection |
| 11 | Client Credentials and machine-to-machine flow |
| 12 | private_key_jwt, token acquisition, Okta Management API authorization |
| 13 | Browser and authentication troubleshooting path |
| 14 | Token, API, and automation troubleshooting path |
| 15 | Complete capstone architecture and end-to-end transaction |

## Diagram style

Use:

- `flowchart` for architecture, ownership, and decision paths
- `sequenceDiagram` for transactions over time
- small tables when comparing components or token responsibilities
- simple text diagrams only when they are faster to read than Mermaid

Keep each diagram focused on one question. Do not put every OAuth concept into one picture.
