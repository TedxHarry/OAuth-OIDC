---

# Part 13 — Project intake: what to ask before you implement

This is the checklist you should use in a real project meeting.

## Application shape

- SPA, native/mobile, server-side web app, API, background service, or combination?
- What framework/language is used?
- Who owns frontend, backend, API, and Okta configuration?

## User and access model

- Is there an end user in the flow?
- Workforce users, customers, partners, or service accounts?
- Is this authentication, API authorization, or both?
- Which users/groups should access the application?

## OAuth/OIDC design

- Redirect or embedded authentication?
- Which authorization server?
- Which flow/grant type?
- Which redirect and logout URIs for each environment?
- Which scopes are required?
- Which claims does the application actually need?
- What is the API audience?
- Does the application need refresh tokens?
- How should the client authenticate?

## API behavior

- Which API endpoints require which scopes/roles?
- How will access tokens be validated?
- Local JWT validation or introspection where current revocation state matters?
- Expected 401 vs 403 behavior?

## Authentication policy

- Existing Global Session Policy?
- Existing App Sign-In/Authentication Policy?
- MFA or authentication-assurance requirement?
- Existing routing/external IdP behavior that could affect login?

## Operations

- Dev/test/prod Okta orgs or apps?
- Who owns client secret/private key storage?
- Rotation requirement?
- Monitoring and System Log access?
- Change-management/promotion process?
- API Access Management licensing available if Custom Authorization Server is required?

This checklist keeps you from discovering architectural requirements halfway through implementation.
