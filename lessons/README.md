# Lessons

Work through these in order.

The reader is assumed to be new to OAuth/OIDC. Each lesson must teach the concept before asking the reader to configure or troubleshoot it.

The order is:

1. requirement
2. explanation
3. why it exists
4. diagram or transaction
5. successful example
6. hands-on work when useful
7. break/fix
8. troubleshooting
9. explain-back

The goal is understanding first. Hands-on work is used to make that understanding concrete.

1. [Day 1 - Core logic and architecture](day-01-core-logic-and-architecture.md)
2. [Day 2 - Read the HTTP transaction](day-02-http-transaction.md)
3. [Day 3 - Authorization Code + PKCE](day-03-authorization-code-pkce.md)
4. [Day 4 - ID, access, and refresh tokens](day-04-tokens-and-refresh.md)
5. [Day 5 - JWT, discovery, JWKS, and validation](day-05-jwt-validation.md)
6. [Day 6 - Okta application configuration and client authentication](day-06-app-types-client-auth.md)
7. [Day 7 - Server-side Web App vs Browser SPA](day-07-web-app-vs-spa.md)
8. [Day 8 - Protect the API](day-08-protect-api.md)
9. [Day 9 - Authorization servers, scopes, claims, groups, and policies](day-09-authorization-design.md)
10. [Day 10 - Sessions, UserInfo, logout, revocation, and introspection](day-10-session-token-lifecycle.md)
11. [Day 11 - Client Credentials and machine-to-machine](day-11-client-credentials.md)
12. [Day 12 - Okta Management API automation](day-12-okta-api-automation.md)
13. [Day 13 - Browser and authentication troubleshooting](day-13-browser-auth-troubleshooting.md)
14. [Day 14 - Token, API, and automation troubleshooting](day-14-token-api-and-automation-troubleshooting.md)
15. [Day 15 - Capstone](day-15-capstone-operate-like-the-implementation-engineer.md)

## Working rule

Do not move on because a section makes sense while reading it. Move on when you can:

- explain why it exists
- draw the transaction
- identify what the browser, application, Okta, and API are each doing
- configure or implement it
- break it deliberately
- locate the failed step
- prove the cause from evidence
- explain the root cause in plain language
