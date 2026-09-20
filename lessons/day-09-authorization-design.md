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

For Custom Authorization Server access-policy rules, Okta treats the reserved OIDC scopes as built-in scopes. The important Day 9 allowlist work is restricting our custom API scopes such as employee.read and salary.read.

This is why the lab rule configuration focuses on the custom scopes instead of asking you to recreate openid as a custom scope.

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
Assigned the app and a member of Employee-API-HR

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



## ID-token claim vs access-token claim

Our Day 9 claims are configured for:

~~~text
Access Token
~~~

Therefore you should not automatically expect them in:

~~~text
ID Token
~~~

Token Preview makes this visible.

This matters because:

~~~text
ID token
-> client authentication result

Access token
-> API authorization credential
~~~

Choose claim placement based on the intended consumer.

## Token Preview

The Custom Authorization Server page includes Token Preview.

It lets you vary request properties such as:

~~~text
OAuth/OIDC client
grant type
user
scopes
~~~

and inspect the resulting token content or errors.

This is useful for debugging:

~~~text
claim expression
group filter
scope inclusion
policy and rule matching
token lifetime
claim placement
~~~

Before running a full browser flow, Token Preview can answer:

> Given this client, user, grant type, and scope request, what does the authorization server think it should produce?

## Token Preview is not the whole integration

Token Preview does not prove:

~~~text
browser redirect works
registered redirect URI is correct
PKCE transaction state survives
application callback works
application token storage works
resource server accepts the token
~~~

Use:

~~~text
Token Preview
-> authorization-server configuration evidence

Real Authorization Code flow
-> client and token issuance evidence

Employee API request
-> resource-server enforcement evidence
~~~

Do not stop at Preview.

## Preview test 1: HR salary token

Use:

~~~text
Client:
Employee Portal SPA

Grant type:
Authorization Code

User:
test user in Employee-API-HR

Scopes:
openid
employee.read
salary.read
~~~

Expected access-token properties include:

~~~text
aud = api://employee-service
scp includes employee.read
scp includes salary.read
department = HR
groups includes Employee-API-HR
token lifetime approximately 15 minutes
~~~

That tells us the HR rule matched.

## Preview test 2: HR user requests employee.read only

Use the same HR user.

Scopes:

~~~text
openid
employee.read
~~~

Expected:

~~~text
employee.read present
salary.read absent
groups claim present
department claim absent
~~~

This proves:

~~~text
HR membership
does not automatically insert salary.read
~~~

The client did not request salary.read.

## Preview test 3: claim placement

Preview the ID token for the same transaction.

Our custom Day 9 claims were configured for:

~~~text
Access Token
~~~

Therefore do not expect:

~~~text
department
groups
~~~

to automatically appear in the ID token.

Token-type placement is configuration.

## Preview test 4: non-HR salary request

Temporarily remove the test user from:

~~~text
Employee-API-HR
~~~

Use a fresh Token Preview or authorization request for:

~~~text
salary.read
~~~

Expected:

~~~text
no matching rule permits salary.read
~~~

The request should fail rather than mint a salary token.

Record the actual error shown by your tenant.

Do not replace evidence with a memorized error string.

## Groups do not become scopes

This is worth repeating.

~~~text
Employee-API-HR membership
        |
        v
can make HR policy rule match
        |
        v
rule can permit requested salary.read
        |
        v
token scp contains salary.read
~~~

Not:

~~~text
Employee-API-HR
        |
        v
salary.read automatically inserted
~~~

That distinction prevents a large class of authorization misunderstandings.

## Claims do not become scopes either

Likewise:

~~~text
department = HR
~~~

does not automatically mean:

~~~text
salary.read
~~~

The department claim is contextual information.

The authorization-server policy and the requested scope determine whether salary.read can be issued in our design.

## Authentication policy is a different layer

Do not troubleshoot every Okta policy from the same place.

### Authentication and session layer

Examples:

~~~text
Global Session Policy
App Sign-In or Authentication Policy
MFA requirements
reauthentication
assurance
Okta browser session
~~~

These answer:

> How must the user authenticate?

### Custom Authorization Server layer

Examples:

~~~text
client covered by policy
grant type
user or group rule
requested custom scopes
token lifetime
rule priority
~~~

These answer:

> May this token request be issued, with which permissions and lifetime?

## Example: unexpected MFA

Suppose:

~~~text
salary.read request
        |
        v
unexpected MFA prompt
~~~

Do not begin by changing the Custom Authorization Server access policy.

Start with:

~~~text
Global Session Policy
App Authentication Policy
existing Okta session state
authenticator requirements
~~~

The Custom Authorization Server access policy is not an MFA policy.

## Example: missing salary.read

Suppose:

~~~text
user authenticates successfully
but
salary.read is missing or the request is rejected
~~~

Investigate:

~~~text
Was salary.read requested?
Is salary.read defined on this authorization server?
Which authorization server is the client using?
Which policy covers the client?
Which rule matched first?
Is the user in Employee-API-HR?
Does the matching rule permit salary.read?
Is there an earlier broad rule?
~~~

That is authorization-server troubleshooting.

## Example: department claim missing

Suppose salary.read is present but:

~~~text
department claim missing
~~~

Do not immediately change the access-policy rule.

Check:

~~~text
claim enabled?
token type = Access Token?
expression = user.department?
user.department populated?
Include in = salary.read?
salary.read actually granted?
Token Preview result?
~~~

Token authorization can be correct while a custom claim is configured incorrectly.

## Example: groups claim missing

Check:

~~~text
claim token type
Value type = Groups
filter expression
actual group name
actual user membership
claim enabled
Token Preview
~~~

Do not change salary.read policy until you know the policy caused the problem.

## Complete HR salary issuance chain

~~~text
SPA requests:
openid employee.read salary.read
        |
        v
Employee API Authorization Server
        |
        v
Policy assigned to SPA?
        |
        v
First matching rule?
        |
        v
HR Salary Access
        |
        | user in Employee-API-HR
        | grant type = Authorization Code
        | requested custom scopes allowed
        v
Access token issued
        |
        | aud = api://employee-service
        | scp includes salary.read
        | department included
        | filtered groups included
        | lifetime about 15 minutes
        v
Employee API
        |
        v
validate token
        |
        v
/api/salary requires salary.read
        |
        v
200
~~~

Every step has a different responsibility.

## Non-HR salary request

~~~text
SPA requests salary.read
        |
        v
Policy covers SPA
        |
        v
HR Salary Access rule
user condition fails
        |
        v
Employee Read Access rule
salary.read not permitted
        |
        v
No matching allow rule
        |
        v
Authorization fails
~~~

The API never receives a valid salary token because the authorization server did not mint one.

The API still enforces salary.read if a caller presents a token.

## HR user does not request salary.read

~~~text
User is in Employee-API-HR
        |
        v
SPA requests only employee.read
        |
        v
matching rule permits employee.read
        |
        v
token scp contains employee.read
        |
        v
salary.read absent
~~~

This is the clean proof that membership does not inject the permission.

## Two authorization layers

Our design has:

~~~text
Layer 1
Custom Authorization Server
decides whether salary.read can be issued

Layer 2
Employee API
requires salary.read on /api/salary
~~~

Both are useful.

The authorization server prevents ineligible clients or users from receiving the scope.

The API prevents the operation unless the presented trusted token contains the scope.

## Avoid accidental redundant authorization

A poor first design might say:

~~~text
/salary requires:
salary.read
AND department == HR
AND groups contains Employee-API-HR
~~~

while Okta already grants salary.read only to the intended HR group.

That creates unnecessary coupling and more failure points.

Our first design is:

~~~text
Authorization Server:
HR group controls eligibility for salary.read

Access token:
salary.read records granted permission

Employee API:
salary.read controls /salary access

department and groups:
context for inspection and future design choices
~~~

Keep the first implementation understandable.

## One authorization server per API product is a design guideline, not an endpoint rule

Do not create one authorization server for every API endpoint.

Think at the API product or security-domain level.

Our Employee API contains:

~~~text
/api/employees
/api/salary
~~~

Both belong to:

~~~text
Employee API Authorization Server
audience = api://employee-service
~~~

Scopes distinguish the operations.

The authorization-server boundary identifies the protected API product.

## Do not overstuff the token

The groups claim is useful for learning, but production claims should be intentional.

Ask:

~~~text
Does the consumer need this claim?
Will it change frequently?
Is the information sensitive?
How large can the token become?
Can the application query the information elsewhere?
~~~

Token convenience should not become uncontrolled data duplication.

## Common mistakes

### Mistake 1: Use the Org Authorization Server for the Employee API

Wrong security boundary.

Use a Custom Authorization Server for tokens your own API validates.

### Mistake 2: Keep a generic audience forever

A generic test audience can be useful while learning.

A real API design should use a deliberate audience.

### Mistake 3: Create salary.read and assume it is granted

Scope existence is not authorization.

A matching policy and rule must allow the request.

### Mistake 4: Assume HR membership adds salary.read

Wrong.

In our design, membership makes the HR rule eligible to match.

The client still requests salary.read.

### Mistake 5: Put a broad Any scopes rule above specific rules

Dangerous.

The first matching rule wins.

### Mistake 6: Change a rule after receiving a code and use the old code to test the new rule

Bad test.

Start a fresh authorization transaction.

### Mistake 7: Treat department as the salary permission

Wrong layer.

The API permission is salary.read.

### Mistake 8: Configure a claim for Access Token and expect it in the ID token

Wrong assumption.

Token-type inclusion is explicit.

### Mistake 9: Put every group in the token

Poor design.

Filter to the groups the consumer actually needs.

### Mistake 10: Treat Token Preview as end-to-end proof

Incomplete.

Preview validates authorization-server behavior, not browser, callback, PKCE, application, or API behavior.

### Mistake 11: Troubleshoot MFA inside access-policy rules

Wrong layer.

Authentication policy controls MFA and assurance.

### Mistake 12: Make salary.read a default scope

Sensitive API permissions should remain deliberate in this course.

Keep salary.read explicitly requested.

## What you should be able to explain

1. Why did we create a dedicated Employee API Authorization Server?
2. What does api://employee-service represent?
3. What is the difference between audience and scope?
4. What is the difference between scope and claim?
5. What is the difference between a group and a scope?
6. What does an access policy cover?
7. What does an access-policy rule decide?
8. Why does rule priority matter?
9. What happens if no policy and rule match?
10. Why must the client still request salary.read?
11. What is a default scope?
12. Why are employee.read and salary.read not default scopes?
13. Why is department included only with salary.read in the lab?
14. Why does the groups claim use a filter?
15. Why does Token Preview help?
16. Why does Token Preview not replace a real flow?
17. Why should policy changes be tested with a fresh authorization transaction?
18. Why is unexpected MFA normally not a Custom Authorization Server policy issue?
19. Why does the API still enforce salary.read after Okta already evaluated the issuance policy?

## Day 9 lab

[Day 9 Lab - Design Employee API Authorization](../labs/day-09-authorization-design.md)

You will:

- create a dedicated Employee API Authorization Server
- set audience to api://employee-service
- create employee.read and salary.read
- create Employee-API-HR
- populate the test user's department
- create a department access-token claim
- create a filtered groups access-token claim
- build an HR-specific salary rule
- build a normal employee-read rule
- use different token lifetimes so rule matching is visible
- use Token Preview before the real flow
- prove HR membership does not automatically insert salary.read
- prove a non-HR salary request is denied
- deliberately create a broad earlier rule and prove rule-order impact
- remove the unsafe broad rule
- obtain real access tokens
- call /api/employees and /api/salary
- verify custom claim placement
- correlate evidence across Okta, token contents, and the Employee API

## Day 9 completion standard

Day 9 is complete when you can explain:

~~~text
Client requests salary.read
        |
        v
Dedicated Custom Authorization Server
audience = api://employee-service
        |
        v
Access policy for client
        |
        v
First matching rule
        |
        | HR group condition
        | Authorization Code
        | salary.read permitted
        v
Access token
        |
        | scp contains salary.read
        | custom claims added as configured
        v
Employee API
        |
        | validates token
        | requires salary.read
        v
salary response
~~~

You should also be able to diagnose separately:

~~~text
scope not requested
scope not defined
policy not assigned to client
no rule matched
wrong rule matched first
user not in group
claim expression wrong
claim filtered by scope
group filter wrong
wrong token type
wrong audience
unexpected MFA
~~~

without calling all of them one generic OAuth problem.

## Official references

- [Okta: Authorization servers](https://developer.okta.com/docs/concepts/auth-servers/)
- [Okta: API Access Management](https://developer.okta.com/docs/concepts/api-access-management/)
- [Okta: Create an authorization server](https://developer.okta.com/docs/guides/customize-authz-server/main/)
- [Okta: Configure an access policy](https://developer.okta.com/docs/guides/configure-access-policy/main/)
- [Okta: Customize tokens with custom claims](https://developer.okta.com/docs/guides/customize-tokens-returned-from-okta/main/)
- [Okta: Customize tokens with a groups claim](https://developer.okta.com/docs/guides/customize-tokens-groups-claim/main/)
- [Okta Help: Test your authorization server configuration](https://help.okta.com/oie/en-us/content/topics/security/api-config-test.htm)
