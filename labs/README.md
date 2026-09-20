# Labs

The labs support learning. They are not the starting point of the lesson.

The learner is assumed to be new to OAuth/OIDC. Before a lab asks the learner to configure or troubleshoot something, the lesson must first explain:

- what it is
- why it exists
- what problem it solves
- which component uses it
- what a successful flow looks like

Hands-on work is used when it helps the learner understand the concept more clearly.

## Available now

- [Day 1 - Architecture and requirements](day-01-architecture-and-requirements.md)
- [Day 2 - Read real HTTP requests](day-02-http-basics.md)
- [Day 3 - Authorization Code with PKCE against Okta](day-03-authorization-code-pkce.md)
- [Day 4 - Inspect tokens and refresh them](day-04-token-lifecycle.md)
- [Day 5 - Validate a real Okta ID token](day-05-jwt-validation.md)
- [Day 6 - Compare SPA and Web client authentication](day-06-app-types-client-auth.md)
- [Day 7 - Run a server-side Web Application and browser SPA](day-07-web-app-vs-spa.md)
- [Day 8 - Protect the Employee API](day-08-protect-api.md)
- [Day 9 - Design Employee API authorization](day-09-authorization-design.md)
- [Day 10 - Prove session and token lifecycle](day-10-session-token-lifecycle.md)
- [Day 11 - Machine-to-machine Employee Reporting](day-11-client-credentials.md)

More lab files will be added as we execute each day.

## Working method

For every major topic:

1. Learn the concept first.
2. Review the diagram or request flow.
3. Walk through a successful example.
4. Build the successful flow.
5. Capture the request and response.
6. Save the important token claims or configuration values.
7. Break one thing deliberately only after the normal behavior is understood.
8. Identify the exact failed step.
9. Prove the cause using Network/Postman, token evidence, and Okta System Log when available.
10. Fix the problem.
11. Repeat the transaction and prove the result changed for the expected reason.
12. Explain what happened in plain language.

Do not skip the break/fix step.
