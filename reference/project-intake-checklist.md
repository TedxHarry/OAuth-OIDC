# Project intake: what to ask before you implement

Use this checklist in a real project meeting before selecting flows or configuring Okta.

## Application shape

- SPA, native/mobile, server-side Web Application, API, background service, or combination?
- Is there a Backend for Frontend, API gateway, reverse proxy, or load balancer?
- Which component is the OAuth/OIDC client?
- Which component is the resource server?
- What framework/language is used?
- Who owns frontend, backend, API, and Okta configuration?
- Does browser JavaScript call the protected API directly?

## User and access model

- Is there an end user in each flow?
- Workforce users, customers, partners, or service accounts?
- Is the requirement authentication, API authorization, or both?
- Which users/groups should access the application?
- Is access controlled by app assignment/Controlled Access?
- Which identity facts determine eligibility for higher-risk permissions?
- How quickly must changes to group/profile data affect authorization?

## OAuth/OIDC design

- Redirect or embedded authentication?
- Which authorization server protects each resource?
- Which flow/grant type belongs to each client?
- Which redirect and sign-out URIs are required for each environment?
- Which scopes are required?
- Which scopes are requested by user clients vs machine clients?
- Which claims does the application actually need?
- Which claims are context only, and which are deliberately used for authorization?
- What is the API audience?
- Does the application need refresh tokens?
- Where must `offline_access` be requested?
- How should each client authenticate to the token endpoint?
- Can the runtime actually protect the chosen client credential?
- Is PKCE required or useful in addition to client authentication?

## API behavior

- Which API endpoints require which scopes/roles?
- Which client types are allowed to call each endpoint?
- How will access tokens be validated?
- Which issuer and audience does the API trust?
- How are signing keys discovered and refreshed?
- Is local JWT validation sufficient, or does current revocation state require introspection?
- What should produce 401?
- What should produce 403?
- What safe correlation ID or validation-stage evidence will the API return/log?
- How will raw bearer tokens be kept out of logs?

## Browser, origin, and session behavior

- What is the browser application's origin in each environment?
- Which cross-origin requests will browser JavaScript make?
- Who owns CORS for each target API?
- Does any supported Okta browser operation require an Okta Trusted Origin?
- Are sign-out redirect and Trusted Origin requirements both documented?
- Are browser privacy/third-party-cookie constraints relevant to the chosen architecture?
- Where are SPA tokens/application state stored?
- Would a BFF architecture materially reduce browser token exposure?

## Authentication policy

- Existing Global Session Policy?
- Existing App Sign-In/Authentication Policy?
- MFA or authentication-assurance requirement?
- Reauthentication requirement?
- Existing routing/external IdP behavior that could affect sign-in?
- Are the test and production apps assigned to the intended authentication policies?

## Token and session lifecycle

- What does local logout mean?
- Should full sign-out end the Okta browser session?
- Should refresh capability be revoked on sign-out?
- What access-token lifetime is appropriate?
- What refresh-token lifetime/rotation behavior is expected?
- How does the client retain the newest rotating refresh token?
- What should happen when refresh fails?
- Does the resource server need live revocation awareness?

## Machine-to-machine access

- Is there a scheduled service, daemon, integration, or automation with no user?
- Which protected resource does it call?
- Which service-specific scopes does it actually need?
- Which client-authentication method will it use?
- Where is the secret/private key stored?
- Who owns credential rotation?
- How are access tokens cached/reused until near expiry?
- Does the authorization-server rule correctly use a no-user condition?

## Okta Management API automation

- Is the automation calling Okta itself or the company's own API?
- Is an API Services app required?
- Which minimum `okta.*` scopes are needed?
- Which standard/custom admin role is needed?
- Can the role be limited to specific resource targets/resource sets?
- Will the service use `private_key_jwt`?
- Where will the private key live?
- What is the signing-key rotation process?
- Is the Public client app admins org setting enabled, and could it accidentally grant Super Administrator?
- Is any DPoP requirement enabled that the client must support?

## Environment separation

- Separate dev/test/prod Okta orgs or separate apps in one org?
- Separate client IDs?
- Separate Custom Authorization Server IDs/issuers?
- Separate audiences?
- Separate redirect/sign-out URIs?
- Separate browser origins?
- Separate secrets/keys?
- Separate admin-role/resource assignments?
- What configuration is promoted vs recreated?
- How will cross-environment combinations be prevented?

## Operations

- Who owns client secret/private key storage?
- Rotation requirement?
- Monitoring and System Log access?
- Which System Log correlation fields will be useful?
- API/application correlation ID?
- Which failures should alert instead of retrying?
- Which transient failures may use bounded retry/backoff?
- Change-management/promotion process?
- Rollback/restoration plan for configuration changes?
- API Access Management available in every production environment that requires a Custom Authorization Server?

This checklist is meant to expose missing architecture and operational requirements before implementation, not halfway through troubleshooting.
