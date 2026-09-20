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
