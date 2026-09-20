# Day 15 - Capstone: Operate Like the Implementation Engineer

## Purpose

Day 15 is not another feature lesson.

Days 1 through 14 taught the building blocks.

Today you receive a realistic requirement and must decide:

- what questions are missing
- which components are OAuth clients
- which components are resource servers
- which authorization server belongs to each trust boundary
- which flow belongs to each client
- which permissions are user permissions
- which permissions are machine permissions
- how the API validates tokens
- how refresh and logout should behave
- how dev and prod remain separate
- how the system is operated and troubleshot
- what evidence proves the implementation works

You should not begin by copying an earlier lab.

The goal is to reason from the requirement.

[Open the Day 15 capstone diagrams](../diagrams/day-15-capstone.md)

## The requirement

You are given this project request:

> The company has a React employee portal and a Java API.
>
> Employees sign in with Okta.
>
> All employees can read ordinary employee information.
>
> Only HR employees can read salary information.
>
> A scheduled reporting process also needs API access without a human user.
>
> The React application needs refresh support.
>
> Logout should behave predictably.
>
> Development and production must be separate.
>
> The operations team may later automate selected Okta Management API tasks.
>
> Security wants least privilege, evidence-based troubleshooting, and no credentials in logs.

That is all you receive initially.

Do not open the Okta Admin Console yet.

## Capstone working rule

For every design choice, write:

~~~text
Requirement:
Decision:
Why:
Trust boundary:
Evidence that will prove it:
Failure I would expect if it is wrong:
~~~

The blank space is intentional.

## Phase 1 - Requirement discovery

Before designing OAuth, identify what the requirement does not tell you.

Ask questions in these areas.

### Application architecture

~~~text
Is the React application a browser-only SPA?
Is there a backend-for-frontend?
Where is the Java API hosted?
Who owns each component?
Does the SPA call the Java API directly?
Is there an API gateway or reverse proxy?
~~~

### Users

~~~text
Are employees Okta workforce identities?
How is HR membership represented?
Okta group?
profile attribute?
external source?
How quickly must HR membership changes affect access?
~~~

### API authorization

~~~text
Which endpoints exist?
Which endpoints need ordinary employee access?
Which endpoints need salary access?
Does the scheduled job need salary data?
Does it need the same permission as a human HR user?
~~~

### Token lifecycle

~~~text
How long should access tokens live?
Is refresh required only for the SPA?
What is the expected idle behavior?
What does logout mean to the business?
Local app sign-out?
Okta SSO sign-out?
token revocation?
all of these?
~~~

### Environments

~~~text
Separate Okta orgs or separate applications?
Separate authorization servers?
Separate API hostnames?
Separate client IDs?
Separate keys/secrets?
How are settings promoted?
~~~

### Operations

~~~text
Which failures should alert?
Who can view System Log?
Where are client secrets/private keys stored?
What is the rotation process?
What correlation IDs are available?
Which Okta Management API tasks might be automated later?
~~~

## Do not invent missing business requirements

If the project owner has not decided whether the scheduled process may read salary data, do not silently give it salary permission.

Record:

~~~text
OPEN REQUIREMENT:
Scheduled reporting process salary access
~~~

and use the minimum known permission until the requirement is resolved.

## Phase 2 - Decompose the trust relationships

Before choosing grants, draw the relationships.

Your first drawing should contain:

~~~text
Employee
React SPA
Okta
Java API
Scheduled Reporting Service
~~~

Show the future Okta automation path separately:

~~~text
Operations Automation
Okta
Okta Management API
~~~

Do not combine the reporting service and Okta Management automation merely because both are machine-to-machine.

They call different resources and use different authorization boundaries.

## Phase 3 - Classify every component

Complete:

| Component | OAuth client? | Public/confidential? | Resource server? | Human user in flow? |
|---|---|---|---|---|
| React SPA |  |  |  |  |
| Java API |  |  |  |  |
| Scheduled reporting process |  |  |  |  |
| Okta |  |  |  |  |
| Future Okta automation |  |  |  |  |

Do this before choosing flows.

A resource server is not automatically an OAuth client.

The Java API is a resource server unless it independently requests tokens for another downstream resource.

## Phase 4 - Choose the authorization boundaries

### Employee API

This is an API the company owns.

Use a Custom Authorization Server because the resource server must validate tokens and the design needs custom scopes, audience, claims, and access policies.

Record:

~~~text
Authorization server name:
Issuer:
Audience:
Protected resource:
~~~

Do not use an Org Authorization Server access token as the credential for the Java API.

### Okta Management APIs

This is a separate future operations path.

Okta API scopes come from the Org Authorization Server.

Do not reuse the Employee API Custom Authorization Server for Okta Management API scopes.

## Phase 5 - Design human-user permissions

Start from API operations.

Candidate scopes:

~~~text
employee.read
salary.read
~~~

Map them:

| Java API endpoint | Required permission |
|---|---|
| GET /employees |  |
| GET /salary |  |

Then answer:

> What fact makes a user eligible to receive salary.read?

Keep these concepts separate:

~~~text
HR group membership
-> eligibility condition

salary.read
-> API permission

department claim
-> optional context
~~~

## Requested then permitted

The intended chain is:

~~~text
React requests salary.read
        |
        v
Authorization Server policy evaluates conditions
        |
        v
HR condition satisfied?
        |
        +-- no -> salary.read not issuable
        |
        +-- yes -> salary.read may be issued
        |
        v
Java API validates token
        |
        v
GET /salary requires salary.read
~~~

Do not teach:

~~~text
User joins HR
-> Okta automatically injects salary.read
~~~

The client requests the scope and policy decides whether it can be issued.

## Phase 6 - Decide whether claims are also needed

A claim can carry context such as:

~~~text
department
employee type
filtered groups
~~~

Ask:

> Does the Java API actually need this fact?

If salary.read alone is sufficient for the endpoint decision, do not add another hidden group check unless the design documents why.

A clean first design is:

~~~text
Authorization Server decides eligibility for salary.read.

Java API enforces salary.read.
~~~

You should also be able to explain a claim-based alternative and where that authorization decision would live.


## Phase 7 - Choose the user flow

For a browser React SPA, decide:

~~~text
flow:
client authentication:
PKCE:
state:
nonce:
~~~

You should be able to justify why a browser public client cannot safely rely on a protected client secret.

The successful transaction should be drawable from memory:

~~~text
React SPA
   |
   | authorization request
   | state + nonce + PKCE challenge
   v
Okta
   |
   | authorization code
   v
React callback
   |
   | validate state
   | code + verifier
   v
/token
   |
   | access token
   | ID token
   | refresh token when designed
   v
React SPA
~~~

## Phase 8 - Design refresh deliberately

The requirement says the React application needs refresh support.

For Authorization Code, request:

~~~text
offline_access
~~~

on the authorization request when a refresh token is expected.

For the SPA, account for rotating refresh-token behavior.

Your design must answer:

~~~text
Where is the current refresh token held?
How is the newest rotating token retained?
What happens when refresh fails?
When is interactive authentication restarted?
How are tokens kept out of logs?
~~~

Do not increase access-token lifetime just to avoid implementing refresh correctly.

## Phase 9 - Define logout before implementing it

Clean logout is not one setting.

Define the expected state changes.

| State | Local logout | Full sign-out option |
|---|---|---|
| SPA local auth state |  |  |
| Okta browser session |  |  |
| Access token current state |  |  |
| Refresh token current state |  |  |

Answer:

~~~text
After local logout, is immediate Okta SSO acceptable?
Should full sign-out end the Okta browser session?
Should refresh capability be revoked?
Does the API require live revocation awareness?
~~~

Do not promise:

~~~text
logout instantly invalidates every already-issued JWT at every locally validating API
~~~

unless your design actually provides that property.

## Phase 10 - Design the scheduled service separately

The scheduled process has no human user.

Expected transaction shape:

~~~text
Scheduled service
        |
        | Client Credentials
        v
Employee API Custom Authorization Server
        |
        | machine access token
        v
Java API
~~~

Choose a service-specific permission.

Candidate:

~~~text
employee.report.read
~~~

Do not automatically reuse salary.read unless the reporting requirement truly needs the salary resource.

Permissions should describe the operation the service needs.

## Service client authentication

The scheduled service is confidential.

For the course design, the established pattern is:

~~~text
client_secret_basic
~~~

against the Employee API Custom Authorization Server.

Record:

~~~text
client ID:
credential storage location:
rotation owner:
scope:
policy:
token lifetime:
~~~

Do not put the secret in source control.

## Machine access policy

The Custom Authorization Server policy should deliberately match:

~~~text
service client
Client Credentials grant
No user
service scope
~~~

Do not depend on a user group for a no-user Client Credentials flow.

## Phase 11 - Design Java API trust

The Java API is a resource server.

Its trust configuration begins from known configuration:

~~~text
trusted issuer
expected audience
accepted client boundary when used
required endpoint scopes
~~~

Then use discovery and JWKS from that trusted issuer.

Validation pipeline:

~~~text
Bearer token present
        |
        v
acceptable JWT/header
        |
        v
trusted JWKS key
        |
        v
signature
        |
        v
issuer
        |
        v
audience
        |
        v
time
        |
        v
other required structural/client checks
        |
        v
TOKEN TRUSTED
        |
        v
endpoint authorization
~~~

Never authorize from an unvalidated token payload.

## API authorization table

Complete this before implementation:

| Endpoint | Accepted client type | Required scope | Expected denial |
|---|---|---|---|
| GET /employees |  |  |  |
| GET /salary |  |  |  |
| GET /reports or equivalent |  |  |  |

Decide whether human and machine clients share endpoints or use distinct endpoints.

Document the choice.

## 401 and 403 requirement

Your Java API must distinguish:

~~~text
401
-> bearer credential not accepted

403
-> bearer credential accepted, operation not permitted
~~~

The API should return useful safe diagnostics such as:

~~~text
WWW-Authenticate
correlation ID
~~~

without returning the bearer token.

## Phase 12 - Design dev and prod as separate trust systems

Do not think of production as only development with a different URL.

Create a configuration matrix.

| Setting | Development | Production |
|---|---|---|
| Okta org/domain |  |  |
| SPA client ID |  |  |
| SPA redirect URI |  |  |
| SPA sign-out URI |  |  |
| Custom AS issuer |  |  |
| Custom AS ID |  |  |
| API audience |  |  |
| HR group identifier/name |  |  |
| Reporting service client ID |  |  |
| Reporting credential/key |  |  |
| API URL |  |  |
| allowed browser origin |  |  |
| access policies |  |  |
| token lifetimes |  |  |
| secret/key store |  |  |
| monitoring destination |  |  |

Some values should differ.

The requirement is internal consistency within each environment.

## Cross-environment mistakes to prevent

Examples:

~~~text
prod SPA client ID
+
dev issuer
~~~

~~~text
prod Java API
+
dev audience token
~~~

~~~text
prod reporting client ID
+
dev secret
~~~

~~~text
prod token
+
dev issuer/JWKS trust
~~~

Environment configuration is part of OAuth security.

## Phase 13 - Future Okta Management API automation

This is not the scheduled reporting path.

Create a separate future design:

~~~text
Operations Automation
        |
        | private_key_jwt
        v
Org Authorization Server
        |
        | Okta API scope
        v
Okta Management API
        |
        | admin role/resource authorization
        v
operation
~~~

Design record:

~~~text
API Services app
Org Authorization Server
Client Credentials
private_key_jwt
minimum okta.* scopes
minimum admin role/custom role
resource target/resource set when applicable
protected private-key storage
rotation process
~~~

Do not assign Super Administrator merely because automation becomes easier.

## Phase 14 - Define observability before testing

For the browser path, plan to capture:

~~~text
Browser Network
Browser Console
safe callback evidence
safe token metadata
Okta System Log
~~~

For Java API requests:

~~~text
HTTP status
WWW-Authenticate
correlation ID
validation stage
required scope
~~~

For machine clients:

~~~text
grant type
client ID
requested scopes
/token HTTP
expires_in
API HTTP
correlation ID
~~~

For Okta API automation:

~~~text
client assertion metadata
kid
scope request
Org-AS token response status
Okta request ID
admin-role/resource configuration
~~~

Never require raw credentials for ordinary troubleshooting.

## Phase 15 - Define success before building

A project is not complete because login works.

Your acceptance evidence should include all relevant rows:

| Test | Expected |
|---|---|
| Assigned employee authenticates | success |
| employee.read token reaches /employees | 200 |
| employee.read-only token reaches /salary | 403 |
| HR user requests and receives salary.read | allowed |
| salary.read token reaches /salary | 200 |
| non-HR user attempts salary.read | denied at authorization boundary |
| API receives ID token | 401 |
| API receives wrong audience token | 401 |
| refresh works | success |
| revoked refresh token is used | refresh fails |
| local logout behavior | matches documented expectation |
| full sign-out behavior | matches documented expectation |
| reporting service gets machine token | success |
| reporting service calls permitted endpoint | success |
| reporting service asks for disallowed scope | denied |
| dev token is sent to prod API | rejected |
| secrets/tokens appear in normal logs | must not happen |

You may add tests based on your final design.

## Phase 16 - Build the happy paths first

Implement and prove, in this order:

~~~text
1. Employee browser sign-in
2. employee.read API access
3. HR salary access
4. non-HR salary denial
5. refresh
6. defined logout behavior
7. scheduled service token acquisition
8. scheduled service API access
9. environment separation
10. future Okta automation design record
~~~

Do not deliberately break a flow that has never worked successfully.

## Phase 17 - Break the system without being told the answer

After every happy path is proven, diagnose at least twelve failures.

Do not label them by category before investigation.

Use failures from different layers:

~~~text
browser authorization
callback transaction
token endpoint
token validation
API authorization
refresh lifecycle
machine client
environment configuration
Okta API automation
~~~

For every failure use:

~~~text
Observed symptom:
Last confirmed successful step:
First failed step:
Evidence:
Root cause:
One change:
Proof after change:
~~~

## Capstone troubleshooting standard

Your first response to an unfamiliar failure should be a request for evidence or a direct inspection of the failed transaction.

It should not be:

~~~text
Try adding a Trusted Origin.
Try changing the policy.
Try regenerating the secret.
Try clearing cookies.
Try assigning Super Admin.
~~~

without proof that the corresponding layer failed.

## Phase 18 - Explain the solution to three audiences

### Application owner

Explain:

~~~text
who signs in
what users can do
what HR users can do
what the scheduled service can do
what logout means
how dev/prod are separated
~~~

Avoid protocol detail unless needed.

### Developer

Explain:

~~~text
issuer
client IDs
redirect URI
Authorization Code + PKCE
state/nonce
scopes
refresh
token validation
401/403
Client Credentials
correlation IDs
~~~

### IAM/security engineer

Explain:

~~~text
trust boundaries
authorization servers
policy conditions
least privilege
client authentication
token lifecycle
refresh rotation
JWKS/key rotation
admin roles/resources
logging and evidence
environment isolation
~~~

If the underlying design changes when you explain it to another audience, the design is not stable.

## Phase 19 - Produce the project handoff

Your capstone handoff should contain:

~~~text
1. Requirement summary
2. Open questions/assumptions
3. Architecture diagram
4. Trust-boundary table
5. Client/resource classification
6. Authorization-server design
7. Scope/claim design
8. Access-policy design
9. SPA integration values
10. Java API validation requirements
11. Scheduled-service design
12. Refresh/lifecycle design
13. Logout behavior
14. Dev/prod matrix
15. Secret/key ownership
16. Monitoring/logging plan
17. Acceptance-test evidence
18. Troubleshooting evidence for broken cases
19. Rollback/restore notes for temporary tests
20. Future Okta API automation design
~~~

A future engineer should be able to operate the integration from this handoff.

## Phase 20 - Reference architecture

Do not read this section until you have produced your own design.

<details>
<summary>Open the reference architecture only after your design is complete</summary>

A clean baseline is:

~~~text
React SPA
  |
  | Authorization Code + PKCE
  | openid profile email offline_access
  | employee.read
  | salary.read when requested
  v
Employee API Custom Authorization Server
  |
  | user/group policy determines which requested scopes may be issued
  v
React SPA
  |
  | Bearer access token
  v
Java API
  |
  | validate signature, issuer, audience, lifetime
  | require employee.read for /employees
  | require salary.read for /salary
  v
Protected resources
~~~

Scheduled-service path:

~~~text
Reporting Service
  |
  | Client Credentials
  | client_secret_basic
  | employee.report.read
  v
Employee API Custom Authorization Server
  |
  | service access token
  v
Java API
  |
  | validate machine token
  | enforce employee.report.read
  v
Reporting resource
~~~

Future Okta automation:

~~~text
Operations Automation
  |
  | Client Credentials
  | private_key_jwt
  v
Org Authorization Server
  |
  | minimum Okta API scopes
  v
Okta Management API
  |
  | service-app admin role/resource authorization
  v
Selected management operation
~~~

</details>

## What you should be able to defend

1. Why is the React SPA public?
2. Why is the Java API a resource server?
3. Why does the Java API use Custom-AS tokens?
4. Why does future Okta API automation use the Org Authorization Server?
5. Why does the SPA use Authorization Code + PKCE?
6. Why is salary.read requested rather than automatically injected by HR membership?
7. What role does the HR condition play?
8. Why is a claim not automatically a permission?
9. Why is offline_access on the authorization request?
10. What does refresh rotation require from the SPA?
11. What does local logout end?
12. What does Okta browser logout end?
13. Why can a locally validated JWT remain usable until expiry after revocation?
14. Why does the scheduled service use Client Credentials?
15. Why should the service normally have its own scope?
16. Why does the machine policy use No user?
17. What does the Java API validate before reading scopes?
18. What produces 401?
19. What produces 403?
20. Why should dev and prod have independent trust configuration?
21. Why is the reporting service different from Okta Management automation?
22. Why does an Okta API service app need both scope grants and admin authorization?
23. What evidence proves each major transaction?
24. What information belongs in a project handoff?
25. How do you find the first failed layer without guessing?

## Day 15 lab

[Day 15 Capstone Lab](../labs/day-15-capstone.md)

The capstone lab intentionally gives fewer instructions than earlier days.

You are expected to reuse the knowledge, scripts, tools, and evidence methods from Days 1 through 14.

## Day 15 completion standard

Day 15 is complete when you can receive the requirement and independently produce:

~~~text
requirements/questions
architecture
flow selection
authorization-server boundaries
scope/policy design
token-validation design
refresh/logout behavior
machine-to-machine design
environment strategy
least-privilege Okta automation design
acceptance evidence
troubleshooting evidence
project handoff
~~~

You should also be able to diagnose failures by saying:

~~~text
Last successful step:
First failed step:
Evidence:
Root cause:
One change:
Proof:
~~~

without being told whether the problem is browser, policy, token, API, refresh, service, or environment related.

## Official references

- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: Authorization Code with PKCE](https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/)
- [Okta: Refresh access tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Okta: Validate access tokens](https://developer.okta.com/docs/guides/validate-access-tokens/main/)
- [Okta: Client Credentials](https://developer.okta.com/docs/guides/implement-grant-type/clientcreds/main/)
- [Okta: Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/)
