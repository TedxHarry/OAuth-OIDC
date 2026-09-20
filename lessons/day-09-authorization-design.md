# Day 9 - Authorization Servers, Scopes, Claims, Groups, and Policies

## Goal for today

Day 8 proved that the Employee API can validate an access token and enforce employee.read.

Day 9 answers the next engineering question:

> How should Okta decide which API permissions and contextual claims belong in that token?

Today you stop treating the authorization server as a black box and design a dedicated authorization boundary for the Employee API.

By the end of Day 9, you should understand:

- Org Authorization Server vs Custom Authorization Server
- why a dedicated API audience matters
- why one authorization server can represent an API product or security domain
- custom scopes
- requested scope vs permitted scope vs granted scope
- default scopes and why they are an explicit exception
- access policies
- access-policy rules
- policy and rule priority
- group-based rule conditions
- token lifetime as a policy result
- custom access-token claims
- Okta Expression Language claims
- filtered groups claims
- claim inclusion by scope
- Token Preview
- why Token Preview does not replace a real flow
- why groups do not automatically become scopes
- why claims do not automatically become permissions
- why authentication and MFA policy are different from Custom Authorization Server policy
- why policy changes should be tested with a fresh authorization transaction

[Open the Day 9 flow diagrams](../diagrams/day-09-authorization-design.md)

## Start with a business requirement

Our Employee Portal now has two API operations.

~~~text
GET /api/employees
-> ordinary employee data
-> requires employee.read

GET /api/salary
-> salary data
-> requires salary.read
-> only HR users should be able to obtain this permission
~~~

The test user also has context that may be useful to applications:

~~~text
department = HR

group membership:
Employee-API-HR
~~~

We now have three different questions.

### Which resource is this token for?

Answer:

~~~text
audience
~~~

### What API operations may this token authorize?

Answer:

~~~text
scopes
~~~

### What useful facts should travel in the token?

Answer:

~~~text
claims
~~~

Do not merge those three concepts.

## Our Day 9 architecture

~~~text
Employee Portal SPA
        |
        | requests employee.read
        | or salary.read
        v
Employee API Authorization Server
        |
        | evaluates client
        | user or group
        | grant type
        | requested scopes
        | rule priority
        v
Access token
        |
        | aud = api://employee-service
        | scp = granted permissions
        | department = contextual claim when configured
        | groups = filtered contextual claim
        v
Employee API
        |
        +-- /api/employees requires employee.read
        |
        +-- /api/salary requires salary.read
~~~

The authorization server decides what token can be issued.

The API still makes the final endpoint authorization decision.

## Why create a dedicated authorization server?

Day 8 used the preconfigured default Custom Authorization Server so we could learn API validation first.

Today we create:

~~~text
Name:
Employee API Authorization Server

Audience:
api://employee-service
~~~

The Employee API is now a deliberate security domain in our design.

Okta recommends making the authorization-server audience specific to the API and commonly organizing custom authorization servers around API products or security domains.

A generic audience such as:

~~~text
api://default
~~~

is useful for training and simple use cases.

A deliberate application architecture should answer:

> Which API or API product is this token intended for?

Our answer is:

~~~text
api://employee-service
~~~

## Audience is not a permission

Do not interpret:

~~~text
aud = api://employee-service
~~~

as:

> The caller may read salary.

Audience tells us the intended resource.

Permission is separate.

~~~text
aud
-> Which resource is this token intended for?

scp
-> Which permissions were granted?
~~~

The Employee API validates both for different reasons.

## Authorization server issuer

When you create a Custom Authorization Server, Okta gives it an ID.

Conceptually:

~~~text
Authorization Server ID:
aus123...

Issuer:
https://YOUR-OKTA-DOMAIN/oauth2/aus123...
~~~

Do not build the issuer by guessing from the server name.

Record the actual issuer displayed by Okta.

Your client and API must use the same authorization-server boundary.

## Scope means requested API access

For our design:

~~~text
employee.read
-> permission to read ordinary employee data

salary.read
-> permission to read salary data
~~~

A scope is not automatically a group.

A scope is not automatically a claim.

A scope is not automatically granted because it exists.

Creating salary.read only defines a permission name that the authorization server can reason about.

## Requested, permitted, granted

This is the core Day 9 rule.

~~~text
Client requests salary.read
        |
        v
Authorization Server evaluates policy and rule
        |
        v
Does the request match an allow rule?
        |
        +-- no -> authorization fails
        |
        +-- yes
              |
              v
salary.read can be granted
              |
              v
access token scp contains salary.read
              |
              v
Employee API can enforce salary.read
~~~

Do not learn this incorrect shortcut:

~~~text
User joins HR group
        |
        v
salary.read magically appears
~~~

Group membership can be a condition that allows a request for salary.read.

The client still requests salary.read in our design.

## Why this distinction matters

Assume Priya is in:

~~~text
Employee-API-HR
~~~

but the SPA requests only:

~~~text
openid employee.read
~~~

Our intended result is:

~~~text
scp:
openid
employee.read
~~~

not:

~~~text
scp:
openid
employee.read
salary.read
~~~

The HR group did not inject salary.read.

It made Priya eligible for a policy rule that can permit salary.read when requested.

## Default scopes are an explicit exception

A custom scope can be marked as a default scope.

If the client omits the scope parameter, Okta can return default scopes that are permitted by the matching access-policy rule.

That means:

~~~text
default scope
-> explicit authorization-server configuration
~~~

It does not mean:

~~~text
group membership
-> hidden scope injection
~~~

For this course:

~~~text
employee.read
salary.read
~~~

are not default scopes.

The client must request them.

## Reserved OIDC scopes vs custom API scopes

Okta already understands reserved OIDC scopes such as:

~~~text
openid
profile
email
offline_access
~~~

Our custom API permissions are:

~~~text
employee.read
salary.read
~~~

A request can contain both.

Example:

~~~text
openid employee.read salary.read
~~~

Keep the conceptual split clear:

~~~text
openid
-> OIDC behavior

employee.read
salary.read
-> our API permission vocabulary
~~~

## Access policy

An access policy belongs to a Custom Authorization Server.

It determines which client applications the contained rules apply to.

For Day 9:

~~~text
Authorization Server:
Employee API Authorization Server

Access Policy:
Employee Portal API Access

Assigned client:
Day 3 Employee Portal SPA
~~~

Another client does not automatically inherit this policy.

## Access-policy rules

Rules define conditions for token issuance.

A rule can evaluate:

~~~text
grant type
user or group condition
requested scopes
token lifetime
~~~

For our first clean design, we create two rules.

### Rule 1: HR Salary Access

~~~text
Priority:
1

Grant type:
Authorization Code

User condition:
Employee-API-HR group

Custom scopes allowed:
employee.read
salary.read

Access-token lifetime:
15 minutes
~~~

### Rule 2: Employee Read Access

~~~text
Priority:
2

Grant type:
Authorization Code

User condition:
users assigned to the client

Custom scopes allowed:
employee.read

Access-token lifetime:
60 minutes
~~~

The intended behavior is:

~~~text
HR users
-> may request salary.read

Other assigned users
-> may request employee.read
-> may not obtain salary.read
~~~

The API still checks the resulting scope.

## Access policies and rules are allowlists

A rule allowing:

~~~text
employee.read
~~~

does not mean:

> Grant everything except salary.read.

It means the matching requests are allowed.

If a non-HR user requests salary.read:

~~~text
HR rule
-> user or group condition does not match

Employee Read rule
-> salary.read is not allowed

Result
-> no suitable rule
-> authorization fails
~~~

This is safer than thinking of policies as deny rules layered over an implicit allow.

## Priority matters

Okta evaluates policies in priority order.

Within a policy, rules are evaluated in priority order.

The first matching policy and rule are applied.

Processing stops.

That creates a common support problem:

~~~text
Specific secure rule
looks correct

but

broader earlier rule
already matched
~~~

The later rule never runs.

## Rule-order example

Suppose we accidentally create:

~~~text
Priority 1
Temporary Broad Rule

User:
Any assigned user

Scopes:
Any scopes

Access-token lifetime:
60 minutes
~~~

above:

~~~text
Priority 2
HR Salary Access

User:
Employee-API-HR

Scopes:
employee.read, salary.read

Access-token lifetime:
15 minutes
~~~

An HR salary request matches the broad rule first.

The HR rule never runs.

A clue can be:

~~~text
Expected salary token lifetime:
15 minutes

Actual token lifetime:
60 minutes
~~~

Worse, a non-HR user can also obtain salary.read while that broad rule exists.

Rule order is not cosmetic.

It changes authorization behavior.

## Why we use different token lifetimes

The different lifetimes provide visible evidence of which rule matched.

~~~text
HR Salary Access
-> 15-minute access token

Employee Read Access
-> 60-minute access token
~~~

When we deliberately add a broad 60-minute rule above the HR rule, Token Preview can expose the wrong match.

## Policy evaluation timing

For Authorization Code flow, policy evaluation belongs to the initial authorization transaction.

Do not change a policy or group condition after an authorization code was already created and then expect the same code redemption to prove the new configuration.

After changes to:

~~~text
policy
rule
rule order
group membership
requested scopes
~~~

start a fresh authorization transaction.

This prevents misleading test results.

## Claims are statements, not permissions by themselves

A claim carries information.

Examples:

~~~text
department = HR

groups = [
  "Employee-API-HR"
]
~~~

A claim can inform application decisions.

Its presence does not automatically create salary.read.

Our first design keeps the responsibilities clear:

~~~text
Access policy
-> decides whether salary.read can be granted

scp
-> records granted API permission

Employee API
-> enforces salary.read

department and groups claims
-> provide contextual information
~~~

Later projects can choose claim-based authorization when that is the deliberate design.

Do not accidentally create two competing authorization systems.

## Custom access-token claims

A Custom Authorization Server lets you define claims for an Access Token or an ID Token.

The same claim does not automatically appear in both.

For Day 9 we create claims specifically for the Access Token.

## Department claim

Set the test user's Okta profile:

~~~text
department = HR
~~~

Then create an access-token claim:

~~~text
Name:
department

Token type:
Access Token

Value type:
Expression

Expression:
user.department

Include in:
salary.read
~~~

Why tie it to salary.read?

Because we want to demonstrate scope-conditioned claim inclusion.

With:

~~~text
openid employee.read salary.read
~~~

the access token can include:

~~~json
"department": "HR"
~~~

With only:

~~~text
openid employee.read
~~~

the department claim should be absent under this configuration.

That is claim inclusion behavior.

It is not API permission enforcement.

## Filtered groups claim

Create another access-token claim.

~~~text
Name:
groups

Token type:
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

The access token can then contain only matching group memberships.

Example:

~~~json
"groups": [
  "Employee-API-HR"
]
~~~

Do not return every group unless the consumer truly needs them.

Okta limits groups claims to 100 groups. A filter producing more than the supported amount can cause the request to fail.

Filter deliberately.

## Why not place every user attribute in a token?

More claims can mean:

~~~text
larger tokens
more exposed context
more coupling to directory attributes
more assumptions in applications
~~~

Include what the consumer actually needs.

A token is not a copy of the whole user profile.

