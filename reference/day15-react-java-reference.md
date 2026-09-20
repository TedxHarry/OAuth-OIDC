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


## React API call

Use the access token, not the ID token.

Representative shape:

~~~javascript
const accessToken = oktaAuth.getAccessToken();

const response = await fetch(
  import.meta.env.VITE_EMPLOYEE_API_URL + "/employees",
  {
    headers: {
      Authorization: "Bearer " + accessToken
    }
  }
);
~~~

Send bearer tokens only to the intended API origins.

Do not put an access token in a URL.

## React route protection

A protected React route should depend on the SDK/application authenticated state.

It should not decide:

~~~text
access token exists
-> user automatically has every API permission
~~~

API permissions still belong to the access token and the resource server.

## Refresh

The original Authorization Code request must include offline_access when refresh-token capability is expected.

The application or SDK must retain the current refresh-token state correctly.

For rotating refresh tokens:

~~~text
RT1 used
  |
  v
new token response
  |
  +-- AT2
  |
  +-- RT2 when rotated
        |
        v
client retains current RT
~~~

Do not keep deliberately using RT1 after RT2 becomes the current token.

## React logout

Separate:

~~~text
clear local SPA auth state
~~~

from:

~~~text
end Okta browser session
~~~

and from:

~~~text
revoke refresh-token capability
~~~

Your project may combine some of these into one user-facing full sign-out action.

For Okta's current React redirect guidance, the SPA origin must be configured as an Okta Trusted Origin for the documented sign-out action.

That Trusted Origin is an Okta-side browser trust setting. It does not configure CORS on the Java API.

Document exactly what the action does.

## Production Custom Authorization Server check

The Employee API design depends on a Custom Authorization Server.

Okta Integrator Free Plan orgs make developer capabilities available for testing, but API Access Management is a production licensing consideration.

Confirm production availability during project intake instead of discovering it during deployment.

## Java API dependencies

With current Spring Boot and Spring Security, the resource server normally needs the OAuth 2.0 Resource Server starter.

Maven dependency shape:

~~~xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
</dependency>
~~~

Use the Spring Boot version supported by your project.

Do not copy a course-pinned framework version into production without checking support.

## Java issuer and audience

Representative application configuration:

~~~yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://YOUR-OKTA-DOMAIN/oauth2/YOUR-AUTHORIZATION-SERVER-ID
          audiences: api://employee-service
~~~

The issuer must be the Employee API Custom Authorization Server.

The audience must match the resource identifier configured for the Employee API.

Do not use the Org Authorization Server issuer for this custom API.

## What Spring Resource Server provides

With issuer-based JWT resource-server configuration, Spring Security can:

~~~text
discover authorization-server metadata
obtain signing keys
validate JWT signature
validate issuer
validate time claims
map OAuth scopes to authorities
handle signing-key rotation
~~~

Current Spring Security maps a scope such as:

~~~text
employee.read
~~~

to an authority shaped like:

~~~text
SCOPE_employee.read
~~~

Audience validation must also be part of the API trust configuration.

## Representative Java security configuration

A simple endpoint authorization shape:

~~~java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/health").permitAll()
                .requestMatchers("/employees")
                    .hasAuthority("SCOPE_employee.read")
                .requestMatchers("/salary")
                    .hasAuthority("SCOPE_salary.read")
                .requestMatchers("/reports")
                    .hasAuthority("SCOPE_employee.report.read")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}));

        return http.build();
    }
}
~~~

The exact Java DSL can vary with the Spring Security version.

The important design is:

~~~text
validate bearer credential
then
apply endpoint permission
~~~

## Representative controller

~~~java
@RestController
public class EmployeeController {

    @GetMapping("/employees")
    public Map<String, Object> employees() {
        return Map.of(
            "employees",
            List.of("E1001", "E1002")
        );
    }

    @GetMapping("/salary")
    public Map<String, Object> salary() {
        return Map.of(
            "message",
            "Salary resource allowed"
        );
    }

    @GetMapping("/reports")
    public Map<String, Object> reports() {
        return Map.of(
            "message",
            "Reporting resource allowed"
        );
    }
}
~~~

Do not put the authorization decision only in controller UI or business logic if Spring Security already owns the endpoint boundary.

## Client boundaries

Scopes describe permission.

Some APIs also deliberately restrict which OAuth clients may call particular endpoints.

If your design requires that additional check, validate the trusted cid claim after JWT validation.

Example design:

~~~text
/employees and /salary
-> allowed SPA client IDs

/reports
-> allowed reporting-service client ID
~~~

Do not read cid from an unvalidated token.

If you do not need a client allowlist, document why policy plus scope is sufficient.

## 401 vs 403

Expected behavior:

~~~text
missing or invalid bearer credential
-> 401

valid bearer token missing required SCOPE_ authority
-> 403
~~~

Test both.

Do not rewrite every denial into the same status.

## Correlation IDs

Add a request correlation ID at the Java API boundary.

Safe log shape:

~~~text
correlation_id=...
path=/salary
result=forbidden
required_scope=salary.read
~~~

Avoid:

~~~text
access_token=...
~~~

A correlation ID should let you connect the client request, Java API response, and Java API server log without exposing credentials.


## CORS ownership

If the React SPA origin differs from the Java API origin:

~~~text
React origin:
https://app.example.com

Java API origin:
https://api.example.com
~~~

the Java API must return the correct CORS response for the React origin.

An Okta Trusted Origin does not configure CORS headers on the Spring Boot API.

Configure the Java API deliberately.

## Representative Spring CORS configuration

One possible shape:

~~~java
@Bean
CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();

    config.setAllowedOrigins(
        List.of("https://app.example.com")
    );

    config.setAllowedMethods(
        List.of("GET", "POST", "OPTIONS")
    );

    config.setAllowedHeaders(
        List.of("Authorization", "Content-Type")
    );

    UrlBasedCorsConfigurationSource source =
        new UrlBasedCorsConfigurationSource();

    source.registerCorsConfiguration("/**", config);

    return source;
}
~~~

Then enable CORS through the Spring Security configuration appropriate to the project.

Do not use wildcard origins casually for a protected API.

## Reporting service reference

The scheduled process is a different client.

Representative token request:

~~~http
POST https://YOUR-OKTA-DOMAIN/oauth2/YOUR-AS-ID/v1/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
scope=employee.report.read
~~~

Expected behavior:

~~~text
access token
no ID token
no user authentication
no browser callback
~~~

The Java API validates that machine token using the same Custom Authorization Server trust boundary and enforces employee.report.read on the reporting endpoint.

## Reporting token cache

The service should not request a new token for every API call.

Conceptual logic:

~~~text
cached token exists and is not near expiry?
        |
        +-- yes -> use token
        |
        +-- no -> request new Client Credentials token
~~~

Protect the client credential.

Do not log it.

## Environment configuration

Use environment-specific values.

React example:

~~~text
VITE_OKTA_ISSUER
VITE_OKTA_CLIENT_ID
VITE_EMPLOYEE_API_URL
~~~

Java example:

~~~text
OKTA_API_ISSUER
OKTA_API_AUDIENCE
ALLOWED_SPA_ORIGIN
~~~

Reporting service example:

~~~text
OKTA_SERVICE_ISSUER
OKTA_SERVICE_CLIENT_ID
OKTA_SERVICE_CLIENT_SECRET
~~~

Production secrets belong in the approved secret-management system.

Do not commit environment-specific credentials to Git.

## Future Okta Management automation

Do not reuse the Employee API service-client pattern.

Reference path:

~~~text
API Services application
Org Authorization Server
Client Credentials
private_key_jwt
minimum Okta API scopes
service-app admin role and resource authorization
~~~

The private key stays with the automation.

Okta stores the public key.

Treat the resulting Org-AS access token as a credential for Okta, not as a custom JWT contract for your own application.

## Reference acceptance tests

The final implementation should prove at least:

~~~text
non-HR employee -> /employees 200
non-HR employee -> /salary denied
HR employee requesting salary.read -> /salary 200
HR employee not requesting salary.read -> salary.read absent
ID token -> Java API 401
wrong audience token -> Java API 401
valid employee.read token -> /salary 403
refresh -> new usable access token
revoked refresh token -> refresh failure
reporting client -> /reports 200
reporting client -> disallowed scope denied
dev token -> prod API rejected
no raw tokens or secrets in normal logs
~~~

## Reference implementation review questions

Before calling your implementation equivalent to this reference, answer:

1. Is the React client still public?
2. Is there any client secret in browser code or browser-delivered configuration?
3. Does the API trust a configured Custom Authorization Server issuer?
4. Is audience validated?
5. Are scopes enforced only after token validation?
6. Does the SPA send the access token rather than the ID token?
7. Is salary.read actually requested by the client?
8. Does policy decide whether HR users may receive salary.read?
9. Does the reporting service use Client Credentials with no user?
10. Does the reporting endpoint require a service-specific scope?
11. Are 401 and 403 distinguishable?
12. Does the Java API own CORS for its own origin?
13. Are refresh tokens handled as credentials?
14. Are dev and prod values kept internally consistent?
15. Is future Okta automation separated from the Employee API machine client?

## Current implementation references

- [Okta: Sign users in to a SPA using the redirect model](https://developer.okta.com/docs/guides/sign-into-spa-redirect/react/main/)
- [Okta: Authorization Code with PKCE](https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/)
- [Okta: Refresh access tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
- [Spring Security: OAuth 2.0 Resource Server JWT](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)
- [Spring Security: OAuth 2.0](https://docs.spring.io/spring-security/reference/servlet/oauth2/)
