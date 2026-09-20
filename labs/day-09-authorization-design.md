# Day 9 Lab - Design Employee API Authorization

## Purpose

Day 8 proved that an API can validate and enforce a scope.

Day 9 designs how Okta decides which scopes and claims can be issued.

You will build:

~~~text
Employee API Authorization Server
Audience = api://employee-service

Scopes:
employee.read
salary.read

Group:
Employee-API-HR

Access-token claims:
department
filtered groups

Rules:
HR Salary Access
Employee Read Access
~~~

Then you will prove the design with Token Preview, real Authorization Code + PKCE flows, and the Employee API.

Complete the lesson first:

[Day 9 - Authorization Servers, Scopes, Claims, Groups, and Policies](../lessons/day-09-authorization-design.md)

Use the diagrams:

[Day 9 Flow Diagrams](../diagrams/day-09-authorization-design.md)

## Safety rules

Do not save or share live credentials:

~~~text
authorization codes
access tokens
ID tokens
refresh tokens
PKCE verifiers
client secrets
session cookies
~~~

Record claims, configuration, HTTP status, rule behavior, and correlation IDs instead.

## Important testing rule

After changing any of these:

~~~text
policy
rule
rule order
group membership
requested scopes
~~~

start a completely fresh authorization transaction.

Do not use an authorization code created before the change.

## Part 1 - Create a dedicated authorization server

In the Okta Admin Console:

~~~text
Security
  |
  v
API
  |
  v
Authorization Servers
  |
  v
Add Authorization Server
~~~

Create:

~~~text
Name:
Employee API Authorization Server

Audience:
api://employee-service

Description:
Authorization server for the OAuth/OIDC training Employee API
~~~

Save.

Record the actual:

~~~text
Authorization Server ID:
Issuer:
Audience:
~~~

The issuer should have a shape similar to:

~~~text
https://YOUR-OKTA-DOMAIN/oauth2/aus...
~~~

Do not derive the ID from the display name.

Use the value Okta created.

## Part 2 - Compare the three authorization-server boundaries you now know

Record:

~~~text
Org Authorization Server issuer:
https://YOUR-OKTA-DOMAIN

Day 8 default Custom AS issuer:
https://YOUR-OKTA-DOMAIN/oauth2/default

Day 9 Employee API AS issuer:
YOUR-ACTUAL-DAY9-ISSUER
~~~

Then answer:

1. Which one mints Okta API access tokens?
2. Which one was our generic Day 8 custom-API training server?
3. Which one now represents the Employee API product?
4. Which audience will the Day 9 Employee API expect?

Do not continue until these are distinct in your mind.

## Part 3 - Create employee.read

Open the new authorization server:

~~~text
Scopes
  |
  v
Add Scope
~~~

Create:

~~~text
Name:
employee.read

Display phrase:
Read employee data

Description:
Read ordinary Employee API data
~~~

For this lab:

~~~text
User Consent:
Implicit

Set as a default scope:
No

Include in public metadata:
optional
~~~

Save.

## Part 4 - Create salary.read

Create:

~~~text
Name:
salary.read

Display phrase:
Read salary data

Description:
Read salary data from the Employee API
~~~

Again:

~~~text
User Consent:
Implicit

Set as a default scope:
No
~~~

We deliberately keep salary.read explicit.

The client must request it.

## Part 5 - Create the HR group

Go to the Groups area in the Admin Console.

Create:

~~~text
Employee-API-HR
~~~

Add your Day 9 test user to the group.

Record:

~~~text
Test user:
HR group membership present?:
~~~

Do not use the Everyone group for this rule.

We need a visible HR-specific condition.

## Part 6 - Set the department profile value

Open the test user's Okta profile.

Set:

~~~text
department = HR
~~~

Save.

The group and department are deliberately separate facts.

~~~text
Employee-API-HR
-> policy-rule condition

department = HR
-> claim source
~~~

This lets us prove that a profile claim and a permission rule are not the same thing.

## Part 7 - Create the department claim

Open:

~~~text
Security
  |
  v
API
  |
  v
Employee API Authorization Server
  |
  v
Claims
  |
  v
Add Claim
~~~

Configure:

~~~text
Name:
department

Include in token type:
Access Token

Value type:
Expression

Value:
user.department

Include in:
salary.read
~~~

Keep the claim enabled.

Save.

Expected behavior:

~~~text
salary.read token
-> department claim can appear

employee.read-only token
-> department claim should be absent
~~~

This is a scope-conditioned claim.

## Part 8 - Create the filtered groups claim

Add another claim:

~~~text
Name:
groups

Include in token type:
Access Token

Value type:
Groups

Filter:
Matches regex

Value:
^Employee-API-.*$

Include in:
Any scope
~~~

Save.

The claim should include only matching group names such as:

~~~text
Employee-API-HR
~~~

It should not dump every group the user belongs to.

Okta limits groups claims, so deliberate filtering also protects token size.

## Part 9 - Create the access policy

Open:

~~~text
Access Policies
  |
  v
Add Policy
~~~

Create:

~~~text
Name:
Employee Portal API Access

Description:
Controls Employee Portal access to Employee API scopes

Assign to:
The following clients

Client:
your Day 3 Employee Portal SPA
~~~

Save.

This policy is now specific to that client.

## Part 10 - Create the HR Salary Access rule

Inside the new policy, add a rule.

Name:

~~~text
HR Salary Access
~~~

Configure the rule so that it applies to:

~~~text
Grant type:
Authorization Code

User:
the condition that limits the rule to Employee-API-HR

Scopes requested:
the following custom scopes

employee.read
salary.read
~~~

Okta Admin Console labels can vary slightly by org version.

The important logic is:

~~~text
user must satisfy Employee-API-HR condition
AND
Authorization Code is used
AND
requested custom scopes are within employee.read and salary.read
~~~

Set:

~~~text
Access token lifetime:
15 minutes
~~~

Leave refresh-token details at their defaults unless your UI requires another selection.

Save.

This should be the highest-priority normal rule.

## Part 11 - Create the Employee Read Access rule

Add a second rule.

Name:

~~~text
Employee Read Access
~~~

Configure:

~~~text
Grant type:
Authorization Code

User:
Any user assigned to the app

Scopes requested:
the following custom scopes

employee.read
~~~

Set:

~~~text
Access token lifetime:
60 minutes
~~~

Save.

Ensure the order is:

~~~text
1. HR Salary Access
2. Employee Read Access
~~~

There should be no Any scopes rule in this policy.

## Part 12 - Explain the expected behavior before testing

Complete this table before touching Token Preview.

| User state | Requested custom scopes | Expected result |
|---|---|---|
| HR member | employee.read | Token allowed |
| HR member | employee.read + salary.read | Token allowed |
| Non-HR assigned user | employee.read | Token allowed |
| Non-HR assigned user | salary.read | Authorization should fail |
| HR member | employee.read only | salary.read must not be injected |

If your expectation differs, review the lesson before proceeding.

## Part 13 - Token Preview: HR salary request

Open:

~~~text
Token Preview
~~~

Select request properties equivalent to:

~~~text
OAuth/OIDC client:
Employee Portal SPA

Grant type:
Authorization Code

User:
your test user

Scopes:
openid
employee.read
salary.read
~~~

Preview.

Record:

~~~text
Preview successful?:
aud:
scp:
department:
groups:
iat:
exp:
approximate lifetime minutes:
~~~

Expected reasoning:

~~~text
salary.read present
department = HR
groups includes Employee-API-HR
lifetime about 15 minutes
~~~

The exact JSON ordering is irrelevant.

## Part 14 - Token Preview: HR employee-read-only request

Keep the same client and HR user.

Change scopes to:

~~~text
openid
employee.read
~~~

Preview again.

Record:

~~~text
scp:
salary.read present?:
department present?:
groups present?:
lifetime:
~~~

Expected:

~~~text
employee.read present
salary.read absent
department absent
groups can remain present
~~~

This is one of the central Day 9 proofs:

~~~text
HR membership
does not automatically add salary.read
~~~

## Part 15 - Token Preview: check ID-token placement

Using a request that can produce an ID token, inspect the ID-token preview.

Look for:

~~~text
department
groups
~~~

Our claims were configured as:

~~~text
Access Token
~~~

so they should not automatically appear in the ID token.

Record:

~~~text
department in access token?:
department in ID token?:
groups in access token?:
groups in ID token?:
~~~

Explain why this is configuration, not randomness.

## Part 16 - Start the callback receiver

From the repository root:

~~~powershell
python scripts/python/day03_pkce_callback_server.py
~~~

Keep it running.

The Day 3 SPA should still allow:

~~~text
http://localhost:8000/callback
~~~

## Part 17 - Obtain a real employee.read token

Use the reusable authorization helper from Day 8.

Run on one line:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid employee.read"
~~~

Open the generated URL.

Complete sign-in.

Verify returned state.

Exchange the fresh authorization code at the token endpoint printed by the helper.

Postman body:

| Key | Value |
|---|---|
| grant_type | authorization_code |
| client_id | SPA client ID |
| redirect_uri | http://localhost:8000/callback |
| code | Fresh code |
| code_verifier | Matching verifier |

No client secret.

Keep the access token locally.

## Part 18 - Inspect the real employee.read token

Run:

~~~powershell
python scripts/python/day09_inspect_access_token.py
~~~

Record:

~~~text
iss:
aud:
cid:
scp:
department:
groups:
lifetime_minutes:
~~~

Expected:

~~~text
aud = api://employee-service
employee.read present
salary.read absent
department absent
groups includes Employee-API-HR
~~~

The lifetime may reflect whichever valid rule matched your configuration.

Use it as evidence.

## Part 19 - Obtain a real HR salary token

Start a new authorization transaction:

~~~powershell
python scripts/python/day08_prepare_api_authorization.py --issuer YOUR-DAY9-ISSUER --client-id YOUR-SPA-CLIENT-ID --scope "openid employee.read salary.read"
~~~

Complete the flow with the same HR test user.

Use the matching verifier when exchanging the fresh code.

Keep the new access token locally.

## Part 20 - Inspect the real salary token

Run:

~~~powershell
python scripts/python/day09_inspect_access_token.py
~~~

Record:

~~~text
iss:
aud:
cid:
scp:
department:
groups:
lifetime_minutes:
~~~

Expected:

~~~text
aud = api://employee-service
employee.read present
salary.read present
department = HR
groups includes Employee-API-HR
lifetime about 15 minutes
~~~

If the lifetime is around 60 minutes instead, investigate which rule matched before continuing.

## Part 21 - Start the Day 9 Employee API

Stop the Day 8 API if it is still using port 7000.

Set:

~~~powershell
$env:OKTA_API_ISSUER="YOUR-DAY9-ISSUER"
$env:OKTA_API_AUDIENCE="api://employee-service"
$env:OKTA_EXPECTED_CLIENT_ID="YOUR-SPA-CLIENT-ID"
~~~

Start:

~~~powershell
python scripts/python/day09_employee_api.py
~~~

Expected endpoints:

~~~text
http://localhost:7000/api/employees
http://localhost:7000/api/salary
~~~

## Part 22 - Call /api/employees with employee.read token

Send:

~~~http
GET http://localhost:7000/api/employees
Authorization: Bearer YOUR-EMPLOYEE-READ-TOKEN
~~~

Expected:

~~~text
200
~~~

Record:

~~~text
HTTP:
X-Correlation-ID:
required_scope:
caller scopes:
caller department:
caller groups:
~~~

The department claim may be absent because this token did not include salary.read.

That does not prevent employee.read authorization.

## Part 23 - Call /api/salary with employee.read-only token

Send the same token to:

~~~http
GET http://localhost:7000/api/salary
~~~

Expected:

~~~text
403
insufficient_scope
required scope = salary.read
~~~

This token can be completely valid and still fail the salary operation.

Record the API correlation ID and log decision.

## Part 24 - Call /api/salary with the HR salary token

Send the salary token:

~~~http
GET http://localhost:7000/api/salary
Authorization: Bearer YOUR-HR-SALARY-TOKEN
~~~

Expected:

~~~text
200
~~~

Record:

~~~text
required scope:
department:
groups:
scopes:
~~~

Important:

The API allowed the operation because:

~~~text
salary.read was present
~~~

not because it independently checked department or groups.

## Part 25 - Prove HR membership does not inject salary.read

Keep the user in Employee-API-HR.

Start a fresh authorization transaction requesting only:

~~~text
openid employee.read
~~~

Inspect the access token.

Record:

~~~text
HR group present in groups claim?:
salary.read in scp?:
~~~

Expected:

~~~text
group can be present
salary.read is absent
~~~

Explain:

~~~text
Group membership affects eligibility.
The client still has to request salary.read.
~~~

## Part 26 - Prove non-HR cannot obtain salary.read

Remove the test user from:

~~~text
Employee-API-HR
~~~

Important:

Start a completely new authorization transaction after the membership change.

Request:

~~~text
openid employee.read salary.read
~~~

Record:

~~~text
Did authorization succeed?:
Did a code get issued?:
OAuth error if any:
Token Preview result:
~~~

Expected design result:

~~~text
No rule should permit salary.read for this user.
No valid salary token should be minted.
~~~

Record the actual error from your tenant rather than forcing a memorized error name.

## Part 27 - Verify normal employee access still works for non-HR

Keep the test user out of Employee-API-HR.

Start a fresh transaction requesting:

~~~text
openid employee.read
~~~

Expected:

~~~text
success
employee.read granted
salary.read absent
approximately 60-minute lifetime
~~~

This proves that removing salary permission did not remove ordinary employee access.

## Part 28 - Restore HR membership

Add the test user back to:

~~~text
Employee-API-HR
~~~

Do not reuse a code from Part 27.

Start a new preview or authorization transaction when testing restored behavior.

Confirm the user can again obtain salary.read under the HR rule.

## Part 29 - Deliberately create a rule-order problem

This is a controlled break/fix exercise.

Create a temporary rule:

~~~text
Name:
TEMP Broad Rule - Delete After Test

Grant type:
Authorization Code

User:
Any user assigned to the app

Scopes requested:
Any scopes

Access-token lifetime:
60 minutes
~~~

Move it above:

~~~text
HR Salary Access
~~~

The temporary order should be:

~~~text
1. TEMP Broad Rule - Delete After Test
2. HR Salary Access
3. Employee Read Access
~~~

Do not leave this configuration in place after the test.

## Part 30 - Prove the broad rule shadows the HR rule

With the user in Employee-API-HR, use Token Preview for:

~~~text
openid employee.read salary.read
~~~

Record:

~~~text
salary.read present?:
token lifetime:
expected HR lifetime:
actual lifetime:
~~~

Expected clue:

~~~text
salary.read can be present
but
lifetime is around 60 minutes
~~~

Why?

~~~text
TEMP Broad Rule matched first.
HR Salary Access was never evaluated.
~~~

This is direct evidence of rule priority.

## Part 31 - Show the security problem with the broad rule

Temporarily remove the user from Employee-API-HR again.

Use Token Preview only.

Request:

~~~text
salary.read
~~~

If the temporary broad rule remains first and allows Any scopes, a non-HR user may now receive permission that the intended design should deny.

Record the actual preview result.

This is why broad rules are dangerous.

Do not obtain or use more real tokens than necessary for this demonstration.

## Part 32 - Fix the rule-order problem

Delete or disable:

~~~text
TEMP Broad Rule - Delete After Test
~~~

Restore the user to Employee-API-HR.

Confirm the safe policy contains only the intended rules:

~~~text
1. HR Salary Access
2. Employee Read Access
~~~

Use Token Preview again.

Expected:

~~~text
HR salary request
-> about 15-minute token

Non-HR salary request
-> denied

Normal employee.read request
-> allowed
~~~

Do not continue until the temporary broad rule is gone.

## Part 33 - Break the department claim safely

Keep the authorization policy correct.

Temporarily disable the:

~~~text
department
~~~

claim.

Use Token Preview for the HR salary request.

Expected:

~~~text
salary.read still granted
department claim absent
~~~

This proves:

~~~text
permission can be correct
while
claim configuration is wrong
~~~

Re-enable the claim.

Preview again.

Expected:

~~~text
department = HR
~~~

## Part 34 - Break the groups filter safely

Temporarily change the groups filter so it does not match:

~~~text
Employee-API-HR
~~~

Use Token Preview.

Expected:

~~~text
salary.read can still be granted
groups claim no longer contains the expected group
~~~

Restore:

~~~text
^Employee-API-.*$
~~~

Preview again.

This proves policy authorization and claim filtering are separate configuration layers.

## Part 35 - Prove Token Preview is not end-to-end proof

Answer:

If Token Preview shows the correct salary.read token, what has it **not** proven?

Include at least:

~~~text
registered callback works
browser redirect works
PKCE verifier survives
real token endpoint exchange works
application storage works
Employee API accepts the token
/api/salary scope enforcement works
~~~

Then state which evidence proves each layer.

## Part 36 - Compare authentication policy vs access policy

For each issue, choose the first policy area to investigate.

### A

User receives an unexpected MFA challenge before the callback.

### B

User authenticates, but salary.read request is rejected.

### C

Token lifetime is 60 minutes when HR rule should create 15 minutes.

### D

User authenticates, salary.read exists, but department claim is absent.

Expected categories:

~~~text
authentication/session policy
authorization-server access policy/rule
claim configuration
~~~

Do not answer every item with Access Policies.

## Part 37 - Prove audience isolation

Stop the Day 9 API.

Set:

~~~powershell
$env:OKTA_API_AUDIENCE="wrong-audience"
~~~

Restart.

Send a still-valid Day 9 salary token.

Expected:

~~~text
401
audience validation failure
~~~

Restore:

~~~powershell
$env:OKTA_API_AUDIENCE="api://employee-service"
~~~

Restart.

If the token is still valid, retry.

Expected:

~~~text
200
~~~

This proves audience is part of the resource-server trust boundary.

## Part 38 - Correlate System Log and API evidence

For one successful salary flow and one denied authorization-server request, collect:

~~~text
Okta System Log
Token Preview
real token inspection
Postman/API response
Employee API log
~~~

For each source, write what it proves and what it does not prove.

Do not expect the API log to explain why Okta refused to mint a token.

Do not expect Okta System Log to explain the Employee API's local 403 after token issuance.

## Part 39 - Final configuration record

### Authorization server

~~~text
Name:
ID:
Issuer:
Audience:
~~~

### Scopes

~~~text
employee.read:
default?:

salary.read:
default?:
~~~

### Group and profile

~~~text
HR group:
test user in HR group?:
department:
~~~

### Claims

~~~text
department:
token type:
expression:
include-in condition:

groups:
token type:
filter:
include-in condition:
~~~

### Access policy

~~~text
Policy name:
Assigned client:
~~~

### Rule 1

~~~text
Name:
Priority:
User/group condition:
Grant:
Allowed custom scopes:
Access-token lifetime:
~~~

### Rule 2

~~~text
Name:
Priority:
User condition:
Grant:
Allowed custom scopes:
Access-token lifetime:
~~~

Confirm:

~~~text
Temporary broad rule removed?:
~~~

## Part 40 - Final behavior matrix

Complete:

| User/request | employee.read | salary.read | department claim | Expected result |
|---|---:|---:|---:|---|
| HR requests employee.read | Yes | No | No | Employee API allowed |
| HR requests salary.read | As requested | Yes | Yes | Salary API allowed |
| Non-HR requests employee.read | Yes | No | No | Employee API allowed |
| Non-HR requests salary.read | No valid salary token | No | Not applicable | Token issuance denied |
| Valid employee token calls salary API | Yes | No | Usually No | API 403 |

Explain why every row behaves that way.

## Part 41 - Explain the design to an application owner

Explain in plain language:

~~~text
We created a dedicated authorization server for the Employee API.

The client asks for specific API permissions.

Okta does not give salary.read just because a person is in HR.

The HR group is used by an access-policy rule to decide whether a request for salary.read is allowed.

If allowed, salary.read is put in the access token.

The API validates the token and then requires salary.read for the salary endpoint.

Department and group claims are extra context, not the permission itself.

The first matching access-policy rule wins, so rule order must be reviewed carefully.
~~~

If you cannot explain that naturally, revisit the diagrams before Day 10.

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Audience

api://employee-service identifies the intended Employee API resource boundary.

### Scope

employee.read and salary.read represent API permissions.

### Group

Employee-API-HR is used as a condition for the HR salary issuance rule.

### Claim

department and groups carry context according to claim configuration.

### Requested scope

Being in Employee-API-HR does not silently add salary.read.

The client requests salary.read and Okta decides whether to permit it.

### Priority

The first matching policy/rule is applied.

An earlier broad rule can bypass the intended specific rule.

### Token Preview

Useful for authorization-server configuration and rule/claim debugging.

Not sufficient for end-to-end proof.

### API

The Employee API validates the token and enforces endpoint scopes.

It does not rely on the frontend or Token Preview.

</details>

## Day 9 completion check

You are ready for Day 10 when you can independently explain and demonstrate:

~~~text
Org AS vs Custom AS
dedicated API audience
requested vs permitted vs granted scopes
default scope exception
access policy
rule allowlist
rule priority
group-based eligibility
scope-based API authorization
custom claims
scope-conditioned claims
filtered groups claims
Token Preview
claim placement
authentication policy vs API access policy
fresh transaction after policy changes
~~~

Do not move on while group membership, claims, and scopes still feel interchangeable.
