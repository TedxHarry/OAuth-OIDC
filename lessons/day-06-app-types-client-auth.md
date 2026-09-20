# Day 6 - Okta App Types and Client Authentication

## Goal for today

So far, you have used one Okta Single-Page Application integration.

Today you learn how to choose the correct Okta application type and how a confidential client proves its identity to the token endpoint.

By the end of Day 6, you should understand:

- what an Okta app integration represents
- why application type must match the component architecture
- SPA, Web, Native, and API Service at a practical level
- public vs confidential client
- client ID vs client credential
- what client authentication means
- none
- client_secret_basic
- client_secret_post
- client_secret_jwt
- private_key_jwt
- why PKCE and client authentication are separate controls
- where redirect URIs, grant types, assignments, and sign-in policy fit
- why an API resource server is not automatically an Okta API Service app
- how the Day 3 SPA configuration differs from a server-side Web Application

[Open the Day 6 flow diagrams](../diagrams/day-06-app-types-client-auth.md)

## Start with architecture, not the Admin Console

Assume a project contains:

~~~text
Employee browser
      |
      v
React frontend
      |
      v
Java backend
      |
      v
Employee API

Nightly Python service
      |
      v
Employee API
~~~

Do not ask:

> Which one Okta app should I create for the whole project?

Ask:

> Which components are acting as OAuth/OIDC clients?

A component is a client when it requests authorization or tokens.

The Employee API may only be a resource server.

The React frontend may be a public client.

The Java backend may be a confidential client.

The Python job may be a machine-to-machine client.

One project can contain several OAuth roles.

## What an Okta app integration represents

An Okta app integration represents an external application or service in the Okta org.

For an OIDC/OAuth client, its configuration can define things such as:

~~~text
client ID
application type
grant types
client authentication method
redirect URIs
sign-out URIs
assignments
application sign-in policy
~~~

Think of it as:

~~~text
Your application component
        |
        | registered relationship
        v
Okta app integration
        |
        v
OAuth/OIDC client configuration
~~~

The integration does not implement the protocol for your application.

Your application still has to use that configuration correctly.

## First decision: can the client protect credentials?

This is the public/confidential question from Day 1.

~~~text
Can the component protect a long-lived client credential
from the end user?

        |
        +-- No --> public client
        |
        +-- Yes --> confidential client
~~~

That decision strongly influences app type and client authentication.

## Single-Page Application

A SPA runs in the browser.

Examples:

~~~text
React
Angular
Vue
browser JavaScript application
~~~

The user can inspect browser-delivered code and traffic.

Therefore:

~~~text
SPA
 |
 v
public client
 |
 v
cannot safely keep client secret
 |
 v
client authentication = none
 |
 v
Authorization Code + PKCE
~~~

This is the app type you created on Day 3.

Okta currently documents Authorization Code for SPAs, with PKCE used when the client has no secret.

## Web Application

A Web Application has a backend component running on infrastructure controlled by the organization.

Examples:

~~~text
Python Flask
Java Spring Boot
ASP.NET
Node or Express server
server-rendered web application
backend-for-frontend
~~~

The browser still participates in redirects, but the backend can protect credentials.

~~~text
Browser
   |
   v
Web Application Backend
   |
   | protected client credential
   v
Okta
~~~

Therefore:

~~~text
Web Application
      |
      v
confidential client
      |
      v
can authenticate itself at /token
~~~

A Web Application can also use PKCE.

That gives two separate protections:

~~~text
PKCE
-> proves possession of the verifier for this authorization transaction

Client authentication
-> proves the registered client identity using its credential
~~~

They are not the same control.

## Native Application

A Native Application is installed on a user's device.

Examples for this course:

~~~text
iOS application
Android application
other installed applications where the client credential would ship to a user-controlled device
~~~

Do not classify every desktop application from the word "desktop" alone.

Desktop deployment models vary. Classify the actual client by asking whether its credentials can truly be protected in that deployment.

The application package is distributed to devices the user controls.

A secret embedded in that package cannot be treated as confidential.

Therefore:

~~~text
Native app
    |
    v
public client
    |
    v
Authorization Code + PKCE
~~~

You do not need to build a native app in this course.

You do need to classify it correctly.

## API Service integration

Okta also has API Service integrations for service access to Okta APIs.

The name can confuse beginners.

An API Service integration represents an OAuth service client.

It is not automatically the same thing as your custom Employee API resource server.

Keep these roles separate:

~~~text
Employee API
-> resource server
-> receives access tokens

API Service integration
-> OAuth client/service
-> requests tokens
-> can be used for service access to Okta APIs
~~~

We use an OAuth service app in Day 12.

Do not create one merely because your architecture contains an API.

## Client ID is not a secret

Every registered OAuth client has a client ID.

Example shape:

~~~text
0oa...
~~~

The client ID tells Okta which registered client is involved.

It is an identifier.

It is not proof of client identity.

A public client can send its client ID.

## What client authentication means

A confidential client can prove its registered identity to an endpoint such as /token.

Conceptually:

~~~text
Client says:
I am client 0oa123

        |
        v

Client supplies proof associated with 0oa123

        |
        v

Okta validates proof

        |
        v

Client authentication succeeds or fails
~~~

The proof depends on the configured method.

## token_endpoint_auth_method

OAuth/OIDC client registration describes the token-endpoint authentication method using the property named token_endpoint_auth_method.

Important methods supported by Okta include:

~~~text
none
client_secret_basic
client_secret_post
client_secret_jwt
private_key_jwt
~~~

You do not need to use all of them now.

You do need to recognize what each means.

## none

none means the client does not authenticate with a protected secret or private key at the token endpoint.

Use it for public clients that cannot protect a credential.

Our Day 3 SPA:

~~~text
client authentication = none
~~~

Its token request included:

~~~text
client_id
authorization code
redirect_uri
code_verifier
~~~

but no client secret.

## client_secret_basic

With client_secret_basic, the client ID and secret are sent using HTTP Basic authentication.

Conceptually:

~~~http
Authorization: Basic Base64(client_id:client_secret)
~~~

The body contains the grant-specific values.

For Authorization Code:

~~~text
grant_type=authorization_code
code=...
redirect_uri=...
code_verifier=...
~~~

The client credential is carried in the Authorization header.

This is the method we use in today's Web Application lab.

Okta's default token endpoint authentication method, when another method isn't specified, is `client_secret_basic`. If a real client has been changed to another authentication method, use that configured method instead of assuming Basic authentication.

## client_secret_post

With client_secret_post, the client credentials are sent as form parameters in the POST body.

Conceptually:

~~~text
client_id=...
client_secret=...
grant_type=...
~~~

This is a different wire format from client_secret_basic.

The client must use the method configured for that client.

Do not randomly move a secret between header and body while troubleshooting.

First check the configured client authentication method.

## client_secret_jwt

With client_secret_jwt, the client uses its shared secret to sign a JWT assertion.

The client sends a client_assertion.

The method is more complex than Basic or POST secret authentication.

For Day 6, recognition-level understanding is enough.

## private_key_jwt

With private_key_jwt, the client signs a JWT assertion using its private key.

Okta has the corresponding public key.

~~~text
Client private key
        |
        | signs client assertion
        v
JWT assertion
        |
        v
Okta verifies using registered public key
~~~

The private key remains with the client.

Only the public key is registered with Okta.

We implement this method in Day 12.

## Shared secret vs private key

### Shared secret

~~~text
Client knows secret
Okta knows secret
~~~

### private_key_jwt

~~~text
Client keeps private key
Okta has public key
~~~

Do not send the private key to Okta.

## Token request examples

### Public SPA

~~~text
POST /token

client_id
code
redirect_uri
code_verifier

No client secret
~~~

### Confidential Web Application with client_secret_basic

~~~text
POST /token

Authorization:
Basic Base64(client_id:client_secret)

Body:
grant_type
code
redirect_uri
code_verifier
~~~

### Confidential client with private_key_jwt

~~~text
POST /token

client_id
client_assertion_type
client_assertion
grant-specific parameters
~~~

The client assertion authenticates the client.

It is not the user's ID token.

## PKCE and client authentication together

A common question is:

> If a Web Application has a client secret, why also use PKCE?

They protect different parts of the transaction.

~~~text
Authorization transaction
        |
        +-- PKCE binds later code redemption
        |   to the verifier created for the transaction
        |
        +-- client authentication proves
            the registered client identity
~~~

Okta's basic Web Application Authorization Code guide demonstrates the confidential-client flow with client authentication. Separately, the current OAuth Security Best Current Practice, RFC 9700, recommends PKCE for confidential clients as protection against authorization-code misuse and injection.

Our Day 6 lab intentionally adds PKCE to the confidential Web Application flow so you can see that PKCE and client authentication are independent checks.

A strong modern baseline is:

~~~text
Web Application
-> Authorization Code
-> PKCE
-> client authentication
~~~

when supported by the chosen library and design.

## Redirect URIs belong to the registered client

A redirect URI answers:

> Where may Okta send the browser authorization response for this client?

Example:

~~~text
http://localhost:8000/callback
~~~

Allowed redirect URIs are registered on the app integration.

The authorization request supplies one of them.

Do not solve redirect failures by adding unnecessary broad callback locations.

Register the callbacks the application actually uses.

## Sign-out redirect URIs

Sign-out redirect URIs are separate from sign-in callbacks.

~~~text
Sign-in redirect URI
-> browser returns after authorization

Sign-out redirect URI
-> browser can return after logout flow
~~~

We study logout on Day 10.

## Grant types

The app integration defines which OAuth grant types are allowed.

Examples:

~~~text
Authorization Code
Refresh Token
Client Credentials
~~~

A client cannot successfully use a grant that it is not configured to use.

Do not enable every grant just in case.

Enable the flows the application actually needs.

## Assignments

In workforce environments, assignment controls which users or groups can access an application integration.

A technically correct OAuth request can still fail if the user is not assigned.

App configuration can therefore include:

~~~text
who can use the app
which sign-in policy applies
which redirect URIs are allowed
which grant types are enabled
how the client authenticates
~~~

We troubleshoot these areas later.

## Application sign-in policy vs authorization-server policy

Do not combine these into one concept.

~~~text
Application sign-in policy
-> authentication requirements

Authorization-server access policy
-> token issuance rules
~~~

We study the policy layers in detail on Day 9.

## Choosing the app type

### React frontend directly performs OIDC

~~~text
Single-Page Application
~~~

### Python or Java backend performs OIDC and protects the credential

~~~text
Web Application
~~~

### Installed mobile application or other user-device client that cannot protect a credential

~~~text
Native Application
~~~

For desktop software, review the actual deployment and credential-protection model before classifying it.

### Non-user service accessing Okta APIs

~~~text
OAuth service / API Service pattern
~~~

The project name does not decide the app type.

The runtime architecture does.

## Authorization server choice is a separate decision

App type answers:

> What kind of OAuth client is this?

It does **not** by itself answer:

> Which authorization server should issue the access token for the resource?

For example:

~~~text
SPA client
or
service client
        |
        v
needs access token for Employee API
        |
        v
authorization server must issue a token intended for Employee API
~~~

The Org Authorization Server tokens used in Days 3 to 5 are intended for Okta.

When we protect our own Employee API, we will use a Custom Authorization Server. That is taught in Day 9.

Do not infer authorization-server choice from app type.

## One system can need more than one app integration

Example:

~~~text
React SPA
-> SPA client integration

Scheduled Okta automation
-> service app integration
~~~

Another design might move token handling to a backend:

~~~text
Browser
  |
  v
Backend-for-Frontend
  |
  v
Okta
~~~

Then the backend may be the OIDC client instead of the browser SPA.

Architecture comes first.

## Common mistakes

### Mistake 1: Choosing Web Application for React because it is a website

Wrong reasoning.

React running entirely in the browser is a public SPA client.

### Mistake 2: Putting a Web Application client secret in JavaScript

Wrong.

The secret belongs only on confidential backend infrastructure.

### Mistake 3: Calling the Employee API an API Service client

Wrong.

The Employee API can be only a resource server.

### Mistake 4: Treating client_id as client authentication

Wrong.

Client ID identifies the client.

A confidential client needs additional proof.

### Mistake 5: Assuming PKCE replaces client authentication for every client

Wrong.

A confidential client can use both.

### Mistake 6: Sending the client secret using the wrong configured method

Wrong.

Use the method configured for the client.

### Mistake 7: Enabling every grant type

Wrong.

Enable only the grants the application needs.

## What you should be able to explain

1. What does an Okta app integration represent?
2. Why is a SPA public?
3. Why is a server-side Web Application confidential?
4. Why is a native app public?
5. What is an API Service integration for?
6. Why is a resource-server API not automatically an API Service client?
7. What does client ID do?
8. What is client authentication?
9. What does none mean?
10. How does client_secret_basic send the credential?
11. How does client_secret_post differ?
12. What are client_secret_jwt and private_key_jwt at a high level?
13. Why can a Web Application use PKCE and client authentication together?
14. What is the purpose of a registered redirect URI?
15. Why should grant types match the requirement?

## Day 6 lab

[Day 6 Lab - Compare SPA and Web Client Authentication](../labs/day-06-app-types-client-auth.md)

## Day 6 completion standard

Day 6 is complete when you can choose the client type from the architecture rather than the project name.

You should also be able to explain:

~~~text
client ID
vs
client credential

PKCE
vs
client authentication

SPA
vs
Web Application

resource server
vs
API Service client
~~~

## Official references

- [Okta: Create an app integration](https://developer.okta.com/docs/guides/create-an-app-integration/-/main/)
- [Okta: Client authentication methods](https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth)
- [Okta: Authorization Code grant](https://developer.okta.com/docs/guides/implement-grant-type/main/)
- [Okta: Authorization Code with PKCE](https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/)
- [Okta: OAuth 2.0 and OpenID Connect overview](https://developer.okta.com/docs/concepts/oauth-openid/)
- [RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)
