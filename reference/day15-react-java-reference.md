# Day 15 Reference Implementation Notes: React SPA + Spring Boot API

## When to use this file

Do not start the capstone by copying this reference.

First complete your own design and as much implementation as possible.

Then use this file to compare:

~~~text
React SPA role
Okta configuration
access-token use
Spring Boot resource-server configuration
scope enforcement
audience validation
CORS ownership
refresh/logout behavior
machine-client separation
~~~

The exact package versions and application framework structure can change over time.

Use current supported Okta and Spring libraries for a real project.

## Reference architecture

~~~text
React SPA
  |
  | Authorization Code + PKCE
  | openid profile email offline_access
  | employee.read
  | salary.read when required
  v
Okta Employee API Custom Authorization Server
  |
  | JWT access token
  v
Spring Boot Java API
  |
  | validate token
  | employee.read -> /employees
  | salary.read -> /salary
  v
protected data
~~~

Machine path:

~~~text
Reporting Service
  |
  | Client Credentials
  | employee.report.read
  v
Employee API Custom Authorization Server
  |
  | JWT machine token
  v
Spring Boot Java API
  |
  | employee.report.read -> /reports
  v
report data
~~~

## React SPA registration

Create the Okta application as:

~~~text
OIDC
Single-Page Application
~~~

Enable:

~~~text
Authorization Code
Refresh Token
~~~

Register the exact environment-specific sign-in and sign-out redirect URIs.

Do not configure the browser SPA as a confidential Web Application merely to obtain a client secret.

The SPA is a public client.

## React libraries

A current Okta React redirect implementation can use:

~~~text
@okta/okta-auth-js
@okta/okta-react
~~~

Use currently supported versions.

Do not freeze the course to an old package version because an older sample uses it.

## Representative React configuration

A configuration object should contain the same concepts as:

~~~javascript
const oidc = {
  issuer: import.meta.env.VITE_OKTA_ISSUER,
  clientId: import.meta.env.VITE_OKTA_CLIENT_ID,
  redirectUri: window.location.origin + "/login/callback",
  postLogoutRedirectUri: window.location.origin + "/",
  pkce: true,
  scopes: [
    "openid",
    "profile",
    "email",
    "offline_access",
    "employee.read"
  ],
  tokenManager: {
    storage: "sessionStorage"
  }
};
~~~

This is a reference shape, not a requirement to use these exact filenames or storage choices.

Your project must choose browser token storage deliberately.

## salary.read should be deliberately requested

Do not assume HR membership adds salary.read automatically.

For the salary operation, the client request must include salary.read and policy must permit it for the HR condition.

Conceptually:

~~~text
requested scopes:
openid
profile
email
offline_access
employee.read
salary.read
~~~

Then:

~~~text
HR user
-> matching policy allows salary.read

non-HR user
-> policy does not allow salary.read
~~~

The important rule is requested then permitted.
