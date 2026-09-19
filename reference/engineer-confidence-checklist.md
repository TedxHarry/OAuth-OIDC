# Engineer confidence checklist

Before you call yourself comfortable with OAuth/OIDC in Okta, you should be able to answer or demonstrate these without guessing.

## Architecture

- I can look at an application and classify each OAuth client.
- I can tell whether there is a user in the flow.
- I can choose Auth Code + PKCE vs Client Credentials.
- I know when I need Org AS vs Custom AS.
- I know OIDC/OAuth does not replace provisioning/SCIM.

## Authorization Code/OIDC

- I can draw the whole browser-to-token flow from memory.
- I can explain `state`, `nonce`, code, verifier, and challenge.
- I can explain why a public client cannot rely on a secret.
- I can explain why a confidential client may use both client authentication and PKCE.
- I know how `offline_access` relates to refresh tokens.

## Tokens

- I know who consumes ID, access, and refresh tokens.
- I never use an ID token as the API authorization credential.
- I can inspect `iss`, `aud`, `exp`, `scp`, and `kid` and know why they matter.
- I can explain local JWT validation vs introspection.

## Okta configuration

- I understand the important OIDC app settings.
- I can configure redirect/logout URIs deliberately.
- I can reason about assignments/Controlled Access.
- I know when Trusted Origins/CORS matters.
- I can configure or troubleshoot the client authentication method.

## Authorization

- I understand scopes, claims, groups, and audience without mixing them.
- I understand that the client requests a scope and the policy permits/denies it.
- I understand access-policy ordering.
- I separate Authorization Server Access Policy from Global Session/App Sign-In Policy.

## API

- I can protect an API with access tokens.
- I can validate signature, issuer, audience, lifetime, and signing key.
- I authorize after validation using scopes/claims appropriate to the API.
- I can reason about 401 vs 403.

## Sessions/lifecycle

- I can explain Okta session vs application session vs tokens.
- I can explain why logout can still result in immediate SSO.
- I can refresh and revoke tokens and explain the expected behavior.
- I understand when local validation will not give me current revocation state.

## Automation

- I can implement Client Credentials for M2M.
- I can implement an Okta API Service app using `private_key_jwt`.
- I understand both Okta API scopes and admin role/resource permissions.
- I can troubleshoot a bad client assertion.

## Troubleshooting

- I follow the transaction instead of changing random settings.
- I can identify whether failure is at `/authorize`, authentication policy, callback, `/token`, token validation, or API authorization.
- I use Network/Postman + token evidence + System Log to prove the cause.
- I can explain the root cause to an application owner in plain language.

If these are true, you have the working model needed for normal implementation-engineer work. The remaining gaps will usually be product-specific or edge-case features that you can learn from vendor documentation when a project actually requires them.

---
