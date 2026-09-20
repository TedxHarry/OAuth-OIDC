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
