# Troubleshooting

The first question for an OAuth/OIDC problem is:

> What is the last step I can prove succeeded?

Then investigate the next step.

## Quick reference

- [Symptom → first areas to investigate](symptom-map.md)

## Investigation order

1. application builds the request
2. browser reaches `/authorize`
3. user authentication and authentication policy
4. callback/authorization response
5. authorization code
6. client calls `/token`
7. tokens are issued
8. client validates the OIDC response
9. client calls the API with an access token
10. API validates the token
11. API authorizes the operation

## Evidence rule

Use these three sources whenever available:

- Network tab, curl, or Postman
- token contents and validation evidence
- Okta System Log

Avoid fixes based only on trial and error. The goal is to identify the failed layer and prove the cause.
