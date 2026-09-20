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

Document exactly what the action does.

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
