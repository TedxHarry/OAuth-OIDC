# Day 15 Capstone Lab

## Purpose

This is the final core-course assessment.

You are expected to reuse knowledge from Days 1 through 14.

The lab intentionally gives fewer procedural instructions.

Your job is to:

~~~text
discover
design
implement
prove
break
diagnose
restore
document
~~~

Complete the lesson first:

[Day 15 - Capstone: Operate Like the Implementation Engineer](../lessons/day-15-capstone.md)

Use the diagrams only after drawing your own first:

[Day 15 Capstone Diagrams](../diagrams/day-15-capstone.md)

## Safety rules

Never place these in notes, screenshots, tickets, or Git:

~~~text
client secrets
private keys
authorization codes
PKCE verifiers
access tokens
refresh tokens
ID tokens
session cookie values
full client assertions
~~~

Use safe metadata and evidence.

## Part 1 - Read the requirement without configuring anything

Use this requirement:

> The company has a React employee portal and a Java API.
>
> Employees sign in with Okta.
>
> All employees can read ordinary employee information.
>
> Only HR employees can read salary information.
>
> A scheduled reporting process needs API access without a human user.
>
> The React application needs refresh support.
>
> Logout must behave predictably.
>
> Development and production must be separate.
>
> Operations may later automate selected Okta Management API tasks.
>
> Security requires least privilege and safe logging.

Do not open the Admin Console yet.

## Part 2 - Produce the missing-questions list

Write at least 15 questions.

Your questions must cover:

~~~text
application architecture
identity source / HR eligibility
API endpoints
machine permissions
refresh behavior
logout behavior
environment separation
secret/key ownership
monitoring
future Okta automation
~~~

Mark every unanswered item as:

~~~text
OPEN
~~~

Do not silently invent a business answer.

## Part 3 - Write explicit assumptions

For the lab, you may proceed with these assumptions if the real project has not answered them:

~~~text
React is a browser SPA.
The SPA calls the Java API directly.
Employees are Okta workforce users.
HR eligibility is represented by Employee-API-HR group membership.
All employees may use employee.read.
Only HR users may receive salary.read.
The reporting process needs employee.report.read only.
The reporting process does not need salary.read.
Development and production use separate OAuth client registrations.
The Java API validates Custom-AS JWT access tokens locally.
~~~

Label them:

~~~text
LAB ASSUMPTIONS
~~~

Do not present them as facts from the original requirement.

## Part 4 - Draw your architecture from memory

Before opening the supplied diagrams, draw:

~~~text
Employee
React SPA
Okta
Employee API Custom Authorization Server
Java API
Scheduled Reporting Service
Future Operations Automation
Org Authorization Server
Okta Management API
~~~

Show arrows and label what crosses each arrow.

Your drawing must distinguish:

~~~text
user authorization path
machine reporting path
future Okta administration path
~~~

## Part 5 - Compare your drawing with the reference diagrams

Now open:

~~~text
diagrams/day-15-capstone.md
~~~

Record:

~~~text
What did I miss?:
What did I connect incorrectly?:
What did I label ambiguously?:
~~~

Correct your own diagram.

Do not simply replace it with the reference.

## Part 6 - Classify every component

Complete:

| Component | OAuth client? | Public/confidential? | Resource server? | Human user? |
|---|---|---|---|---|
| React SPA |  |  |  |  |
| Java API |  |  |  |  |
| Reporting service |  |  |  |  |
| Future operations automation |  |  |  |  |
| Okta |  |  |  |  |

For every row explain why.

## Part 7 - Choose authorization servers

Record:

~~~text
Employee API authorization server type:
Reason:

Employee API issuer:
Employee API audience:

Okta Management API authorization server:
Reason:
~~~

Your answer must keep the Custom Authorization Server and Org Authorization Server separate.

## Part 8 - Design the user scopes

Create a scope table.

| Scope | Resource/action | Requested by | Eligibility |
|---|---|---|---|
| employee.read |  |  |  |
| salary.read |  |  |  |

Then answer:

~~~text
Does HR membership itself become a scope?:
Does HR membership automatically inject salary.read?:
What must the client do?:
What must policy do?:
~~~

## Part 9 - Decide whether claims are needed

For each candidate claim decide:

| Claim | Needed by API? | Context only? | Authorization decision? |
|---|---|---|---|
| department |  |  |  |
| groups |  |  |  |

If salary.read is sufficient for the endpoint decision, say so.

Do not add claims merely because Okta can issue them.

## Part 10 - Design the user policy

Write the policy logic in plain language before configuring it.

At minimum include:

~~~text
client
grant type
user/group condition
requested custom scopes
token lifetime
rule order
~~~

Produce expected outcomes:

| User | Requested custom scopes | Expected |
|---|---|---|
| HR | employee.read |  |
| HR | employee.read + salary.read |  |
| non-HR | employee.read |  |
| non-HR | salary.read |  |
| non-HR | employee.read + salary.read |  |

## Part 11 - Design the React flow

Write:

~~~text
Application type:
Flow:
Client authentication:
PKCE:
state:
nonce:
redirect URI:
sign-out URI:
requested OIDC scopes:
requested API scopes:
refresh requirement:
token storage approach:
~~~

Explain why the browser does not receive a protected client secret.

## Part 12 - Design refresh behavior

Record:

~~~text
offline_access requested where?:
refresh token rotation expected?:
how newest refresh token is retained?:
what happens when refresh fails?:
what causes interactive sign-in again?:
what must never be logged?:
~~~

## Part 13 - Define logout behavior

Write two separate behaviors.

### Local logout

~~~text
SPA local state:
Okta browser session:
refresh capability:
expected next visit:
~~~

### Full sign-out

~~~text
SPA local state:
Okta browser session:
refresh capability:
post-logout redirect:
expected next visit:
~~~

Do not use the phrase logout works without defining the state changes.

## Part 14 - Design the reporting service

Record:

~~~text
client type:
grant:
client authentication:
scope:
authorization server:
human user present?:
credential storage:
rotation owner:
token renewal behavior:
~~~

Explain why the service should not depend on an HR user group.

## Part 15 - Design machine access policy

Write the intended conditions:

~~~text
specific reporting client
Client Credentials
No user
employee.report.read
appropriate token lifetime
~~~

Then answer:

~~~text
Should salary.read be granted to the service by default?:
Why or why not?:
~~~

## Part 16 - Design Java API validation

Record:

~~~text
trusted issuer:
expected audience:
JWKS source:
allowed algorithm:
client boundary for SPA:
client boundary for reporting service:
clock/leeway approach:
raw token logging allowed?:
~~~

Then draw:

~~~text
Bearer
-> key/signature
-> issuer
-> audience
-> time
-> client boundary
-> trusted token
-> scope authorization
~~~

## Part 17 - Map API endpoints to authorization

Complete:

| Endpoint | Human or machine | Required scope | 401 condition | 403 condition |
|---|---|---|---|---|
| GET /employees |  |  |  |  |
| GET /salary |  |  |  |  |
| GET /reports |  |  |  |  |

If your API design differs, document it.

## Part 18 - Design dev and prod

Create:

| Setting | Dev | Prod |
|---|---|---|
| Okta domain/org |  |  |
| SPA client ID |  |  |
| redirect URI |  |  |
| sign-out URI |  |  |
| Custom AS issuer |  |  |
| audience |  |  |
| HR group |  |  |
| reporting client ID |  |  |
| reporting credential store |  |  |
| API URL |  |  |
| browser origin |  |  |
| Okta Trusted Origin when required |  |  |
| API Access Management available |  |  |
| policy/rules |  |  |
| token lifetime |  |  |
| monitoring |  |  |

Mark each field:

~~~text
same by design
or
different by design
~~~

Explain why a dev token must not be accepted by the prod API.


## Part 19 - Define your evidence plan before implementation

For each transaction decide what proves success.

### User browser path

Record:

~~~text
Browser Network evidence:
Callback evidence:
Safe token metadata:
Java API evidence:
Okta System Log evidence:
~~~

### Reporting-service path

Record:

~~~text
/token evidence:
safe token metadata:
Java API evidence:
correlation ID:
~~~

### Lifecycle path

Record:

~~~text
refresh evidence:
revocation/introspection evidence:
logout evidence:
~~~

Do not start testing without knowing what evidence you need.

## Part 20 - Implement the Okta user-side configuration

Using your design, configure the required lab objects.

Your finished user-side configuration should include equivalents of:

~~~text
SPA OIDC application
Employee API Custom Authorization Server
employee.read
salary.read
HR eligibility source
client-specific access policy
ordered policy rules
redirect URI
sign-out URI
Refresh Token grant where required
Controlled Access or assignment appropriate to the lab
~~~

Do not copy values from an earlier environment blindly.

Record only safe identifiers and configuration.

## Part 21 - Implement the Java API resource-server contract

Your Java implementation must enforce the contract you designed.

Minimum required behavior:

~~~text
GET /employees
GET /salary
GET /reports or equivalent machine endpoint

validate access token
validate issuer
validate audience
validate lifetime
use trusted signing keys
enforce endpoint scopes
distinguish 401 and 403
emit a correlation ID
never log the raw bearer token
~~~

If your Java framework performs some checks automatically, document which component performs each check.

Do not claim the API is protected merely because a framework dependency is installed.

## Part 22 - Implement the React SPA contract

The SPA must demonstrate:

~~~text
Authorization Code + PKCE
state handling
OIDC response handling
access token used for Java API
ID token not used as Java API bearer credential
refresh support
local logout behavior
full sign-out behavior when included in your design
no client secret embedded in browser code
~~~

Use a maintained OIDC/OAuth library for the implementation.

The capstone is not testing whether you can hand-write a production protocol client.

## Part 23 - Implement the reporting service

The reporting process must:

~~~text
authenticate as a confidential OAuth client
use Client Credentials
request only its service scope
cache or reuse access token until near expiry
request a new token when needed
call only the permitted Java API operation
avoid logging the client secret or bearer token
~~~

Record:

~~~text
client ID:
scope:
token endpoint:
expires_in:
API status:
correlation ID:
~~~

## Part 24 - Prove ordinary employee access

Use an assigned non-HR test user.

Prove:

~~~text
sign-in succeeds
employee.read is issued when requested
GET /employees returns 200
GET /salary does not succeed with employee.read-only token
~~~

Collect:

~~~text
safe token claims
API correlation ID
API authorization result
relevant Okta evidence
~~~

Do not add the user to HR just to make the test easier.

## Part 25 - Prove HR salary access

Use an HR test user.

Request:

~~~text
employee.read
salary.read
~~~

Prove:

~~~text
HR eligibility condition is satisfied
salary.read is actually requested
salary.read is issued
Java API validates token
GET /salary returns 200
~~~

Record which policy or rule allowed the request.

## Part 26 - Prove HR membership does not inject salary.read

Keep the user in HR.

Start a fresh authorization transaction requesting only:

~~~text
employee.read
~~~

Prove:

~~~text
HR eligibility still exists
salary.read is not present because it was not requested
~~~

This is a required capstone proof.

## Part 27 - Prove non-HR salary denial

Use a non-HR user.

Request salary.read in a fresh transaction.

Expected design:

~~~text
authorization boundary denies salary.read
~~~

Record the actual tenant behavior:

~~~text
authorization outcome:
code issued?:
token issued?:
OAuth error if any:
System Log evidence:
~~~

Do not force a memorized error string.

## Part 28 - Prove 401 and 403 separately

You need at least one real example of each.

### 401 example

Use one of:

~~~text
ID token sent to Java API
wrong audience token
malformed bearer token
expired token
wrong issuer token
~~~

Prove:

~~~text
resource did not accept the bearer credential
~~~

### 403 example

Use:

~~~text
valid employee.read token
to
GET /salary
~~~

Prove:

~~~text
token was trusted
salary.read was missing
operation was denied
~~~

Record the relevant WWW-Authenticate and correlation ID when available.

## Part 29 - Prove refresh behavior

Obtain a refresh token through the normal SPA authorization design.

Record only:

~~~text
refresh token present?:
rotation behavior observed?:
access token expiry:
refresh HTTP:
new access token returned?:
new refresh token returned when applicable?:
~~~

Then prove the SPA uses the current refresh-token state correctly.

Do not deliberately replay an old rotating token unless using a disposable authorization family.

## Part 30 - Prove logout behavior against your written design

Run local logout and compare the result with the Part 13 expectation.

Then run your full sign-out path if implemented.

Record:

~~~text
SPA local state:
Okta browser session:
next protected-route behavior:
refresh capability:
~~~

If actual behavior differs from the design, decide whether the implementation is wrong or the requirement/design must be revised.

Do not change the expected behavior after the test merely to make the test pass.

## Part 31 - Prove scheduled reporting access

Run the reporting process.

Prove:

~~~text
Client Credentials token issued
no human user involved
machine scope present
Java API trusts token
report operation succeeds
~~~

Then request a scope the reporting client should not receive.

Prove token issuance is denied or the operation is denied at the intended boundary.

## Part 32 - Prove environment isolation

Perform at least one safe cross-environment simulation.

Examples:

~~~text
API configured for prod audience
+
dev token
~~~

or:

~~~text
prod-like client configuration
+
dev secret or key
~~~

or:

~~~text
prod API trust
+
dev issuer token
~~~

Prove the system rejects the inconsistent pairing.

Do not weaken prod trust merely to make a dev token work.

## Part 33 - Design future Okta Management automation

Do not implement a broad administrator.

Choose one plausible future operation.

Examples:

~~~text
read selected users
read selected groups
manage membership of one test group
~~~

Design:

~~~text
service app
Org Authorization Server
private_key_jwt
minimum okta.* scope
minimum standard or custom admin role
resource target or resource set where applicable
private key store
key rotation
request or correlation evidence
~~~

Explain why the reporting service credentials cannot simply be reused.

## Part 34 - Create the capstone acceptance matrix

Complete from actual evidence.

| Requirement | Evidence | Pass/Fail |
|---|---|---|
| Employee sign-in |  |  |
| employee.read access |  |  |
| non-HR salary denial |  |  |
| HR salary access |  |  |
| HR membership does not inject unrequested salary.read |  |  |
| Java API token validation |  |  |
| 401 behavior |  |  |
| 403 behavior |  |  |
| refresh |  |  |
| local logout |  |  |
| full sign-out if designed |  |  |
| reporting Client Credentials |  |  |
| reporting least privilege |  |  |
| environment isolation |  |  |
| safe logging |  |  |
| future Okta automation design |  |  |

A row without evidence is not complete.


## Part 35 - Blind incident A

Symptom:

~~~text
Employee clicks Sign in.
Browser reaches Okta.
No callback reaches the React application.
~~~

Write:

~~~text
Last confirmed successful step:
First failed step:
Evidence to collect first:
Three plausible causes:
One change you would NOT make yet:
~~~

Diagnose from the actual system before opening the answer key.

## Part 36 - Blind incident B

Symptom:

~~~text
Callback reaches the SPA.
The token request fails.
The browser client has no client secret.
~~~

Write:

~~~text
Grant type:
What proof or credential is being validated?:
Evidence to collect:
Likely failure layers:
~~~

Do not automatically classify it as invalid_client.

## Part 37 - Blind incident C

Symptom:

~~~text
The Java API returns 401.
The access token has employee.read when decoded.
~~~

Write:

~~~text
Does unvalidated scp prove the token is trusted?:
Validation stages to inspect:
Evidence from WWW-Authenticate or API log:
~~~

Do not add another scope before proving token trust.

## Part 38 - Blind incident D

Symptom:

~~~text
The Java API returns 403 for GET /salary.
The API log says token validation passed.
~~~

Write:

~~~text
First layer to inspect:
Required scope:
Granted scope:
One thing you would NOT rotate:
~~~

## Part 39 - Blind incident E

Symptom:

~~~text
The reporting service receives invalid_client.
No Java API request appears.
~~~

Write:

~~~text
Human authentication relevant?:
Browser CORS relevant?:
Client-authentication evidence:
Credential and configuration pairs to compare:
~~~

## Part 40 - Blind incident F

Symptom:

~~~text
The reporting service receives a token.
The Java API returns 401 with an unexpected client-id stage.
~~~

Write:

~~~text
What upstream step is already proven?:
What should NOT be regenerated first?:
Which Java API trust setting is suspect?:
~~~

## Part 41 - Blind incident G

Symptom:

~~~text
A refresh request worked yesterday.
Today the stored refresh token is rejected.
System Log contains a refresh-token reuse event.
~~~

Write:

~~~text
Which refresh token should the client have stored?:
What rotation behavior must be reviewed?:
What may have happened to newer tokens?:
What should not be replayed repeatedly?:
~~~

## Part 42 - Blind incident H

Symptom:

~~~text
The same application code works in development.
Production API rejects the token for audience.
~~~

Write a comparison containing:

~~~text
issuer
authorization server ID
audience
client ID
API expected audience
~~~

Do not treat identical source code as proof that configuration is identical.

## Part 43 - Blind incident I

Symptom:

~~~text
Future Okta automation obtains a token containing okta.users.read.
GET /api/v1/users is denied.
~~~

Write:

~~~text
Which Day 12 layer is already proven?:
Which authorization layer remains?:
What role or resource evidence is needed?:
Why would a new private key not be the first fix?:
~~~

## Part 44 - Blind incident J

Symptom:

~~~text
The React app signs in successfully.
The API returns 200.
The UI still shows the user as signed out and immediately starts another authorization request.
~~~

Write:

~~~text
Which OAuth/OIDC steps are already proven?:
Which local application state is suspect?:
What browser evidence should be inspected?:
~~~

## Part 45 - Blind incident K

Symptom:

~~~text
Postman can call the Java API.
The React browser call never sends the real GET after OPTIONS.
~~~

Write:

~~~text
What browser control is involved?:
Who owns CORS for the Java API?:
Would an Okta Trusted Origin configure Java API CORS?:
~~~

## Part 46 - Blind incident L

Symptom:

~~~text
A fresh valid token contains a kid not present in the API cached JWKS.
After refreshing the JWKS from the configured trusted issuer, the kid appears.
~~~

Write:

~~~text
Likely cause:
Safe recovery:
Unsafe recovery:
~~~

## Part 47 - Diagnose at least twelve failures in your implementation

Use a mix of:

~~~text
redirect URI
wrong issuer
lost state or transaction
wrong PKCE verifier
unrequested salary.read
non-HR salary request
wrong audience
ID token sent to API
unknown kid
expired access token
revoked refresh token
wrong reporting secret
wrong service scope
wrong expected service client ID
CORS or preflight
local auth-state failure
dev or prod mismatch
Okta API scope vs admin-role failure
~~~

Do not select twelve failures from one layer.

For each create an incident note.

## Part 48 - Restore every temporary break/fix change

Create a restoration checklist:

~~~text
redirect URIs restored
policy order restored
HR membership restored
temporary scopes removed
temporary admin roles removed
API audience restored
API expected client IDs restored
CORS restored
test secrets or keys restored
test group membership restored
browser or app configuration restored
~~~

A troubleshooting lab is not complete while the environment remains intentionally broken.

## Part 49 - Produce the final architecture record

Your handoff must include:

~~~text
architecture diagram
trust-boundary table
component classification
authorization-server mapping
scope table
claim table
policy or rule table
endpoint authorization table
refresh or lifecycle description
logout behavior
machine-client design
dev or prod matrix
future Okta automation design
~~~

Every value should identify its environment.

## Part 50 - Produce the operations record

Include:

~~~text
secret or key owner
storage location
rotation owner or process
token lifetime
monitoring source
System Log access
API correlation-ID location
safe logging rules
failure alerting
retry or backoff behavior
runbook links
~~~

Do not include credentials.

## Part 51 - Produce three explanations

Explain the final implementation to:

### Application owner

No unnecessary protocol detail.

### Developer

Include HTTP, token, callback, and API behavior.

### IAM or security engineer

Include trust boundaries, policies, client authentication, least privilege, lifecycle, rotation, and evidence.

The architecture must remain the same in all three explanations.

## Part 52 - Self-check your design against the reference architecture

Only now open the reference architecture section in:

~~~text
lessons/day-15-capstone.md
~~~

Compare:

~~~text
same important trust boundaries?:
same resource-server distinction?:
same user vs machine separation?:
same Custom-AS vs Org-AS separation?:
same requested-then-permitted scope behavior?:
same validation-before-authorization behavior?:
~~~

Differences are allowed if you can defend them and they still satisfy the requirement securely.


## Part 53 - Blind-incident answer key

Open only after attempting Parts 35 through 46.

<details>
<summary>Expected investigation direction</summary>

### Incident A

Investigate the authorization request before the callback:

~~~text
actual redirect_uri
registered redirect URI
client ID
authorization request error
~~~

Do not begin with Java API authorization.

### Incident B

The browser is a public client.

Investigate the Authorization Code grant:

~~~text
code
PKCE verifier
redirect_uri
issuer or token endpoint
code reuse or expiry
~~~

Do not assume a missing client secret is the defect.

### Incident C

A decoded scope is not trusted evidence until validation succeeds.

Inspect:

~~~text
kid or JWKS
signature
issuer
audience
time
client boundary
~~~

### Incident D

Token trust passed.

Inspect:

~~~text
salary.read
~~~

Do not rotate signing keys.

### Incident E

Client Credentials failed before any Java API call.

Inspect:

~~~text
reporting client ID
configured client-authentication method
secret
environment pairing
~~~

Human MFA and browser CORS are not first-layer causes.

### Incident F

Token acquisition already succeeded.

Inspect:

~~~text
Java API expected service client ID
token cid
environment
~~~

The client secret already worked upstream.

### Incident G

Review rotating-refresh-token handling:

~~~text
newest returned refresh token stored?
old token replayed?
grace period?
reuse detection?
~~~

Do not repeatedly replay the old token.

### Incident H

Compare environment trust:

~~~text
prod issuer
prod audience
token iss
token aud
prod API expectations
~~~

### Incident I

OAuth scope grant already succeeded.

Inspect:

~~~text
service-app admin role
permission
resource target
custom role or resource set
~~~

### Incident J

OAuth/OIDC and API success are already proven.

Inspect:

~~~text
SPA auth-state manager
token manager or storage
route guard
local application state
~~~

### Incident K

This is a browser CORS or preflight path.

Configure CORS on the Java API for the intended SPA origin.

An Okta Trusted Origin does not configure Java API response headers.

### Incident L

The cached JWKS was stale during legitimate key rotation.

Refresh the trusted-issuer JWKS and continue normal validation.

Never disable signature validation.

</details>

## Part 54 - Final engineer confidence review

Revisit:

~~~text
reference/engineer-confidence-checklist.md
~~~

For every item mark:

~~~text
Can explain
Can demonstrate
Need more practice
~~~

Do not mark an item complete merely because you recognize the terminology.

## Part 55 - Final capstone statement

You should now be able to say:

~~~text
I can take an OAuth/OIDC requirement and separate authentication, user API authorization, machine authorization, token lifecycle, and Okta administrative automation.

I can choose the client type, grant, authorization server, scopes, claims, policy, and client authentication based on the actual trust relationship.

I can validate access tokens at the resource server before authorizing from their claims.

I can distinguish 401 from 403, token-endpoint failures from API failures, local JWT validation from live token state, and OAuth scope grants from Okta admin permissions.

I can design refresh and logout behavior deliberately rather than treating them as one operation.

I can keep dev and prod trust configuration separate.

When something fails, I follow the transaction, find the last step I can prove succeeded, identify the first failed layer, change only that layer, and prove the behavior changed.
~~~

If any sentence still feels theoretical, return to the corresponding day and repeat the hands-on proof.

## Day 15 completion check

The core course is complete when you have produced:

~~~text
requirement questions
assumptions
architecture
working user flow
working API authorization
working refresh behavior
documented logout behavior
working machine flow
environment-isolation proof
future Okta automation design
acceptance matrix
at least twelve evidence-based break/fix incident notes
restored lab configuration
project handoff
three audience explanations
~~~

The capstone is not complete if the only proof is:

> Login works.
