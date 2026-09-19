# Day 1 Lab - Read the Requirement Before Choosing a Flow

## Purpose

This lab checks whether you understood the Day 1 lesson.

There is no Okta configuration yet.

You are practicing how an implementation engineer reads a requirement before choosing a flow or creating an application integration.

If you have not completed the lesson, do that first:

[Day 1 - Core OAuth/OIDC Logic and Architecture](../lessons/day-01-core-logic-and-architecture.md)

## Scenario

A company has:

- a React Employee Portal
- a Java Employee API
- Okta for workforce authentication
- a scheduled Python job that also calls the Employee API

The application owner says:

> Employees need to sign in with Okta. The React portal needs to call the Employee API. A scheduled Python job also needs to call the same API every night without a user signing in.

Do not configure anything yet.

First identify the role of each component.

## Part 1 - Classify the components

Complete this table.

| Component | OAuth/OIDC role in this scenario | Human user involved in this client flow? | Public, confidential, or neither? | Main responsibility |
|---|---|---|---|---|
| React Employee Portal |  |  |  |  |
| Java Employee API |  |  |  |  |
| Scheduled Python Job |  |  |  |  |
| Okta |  |  |  |  |

A useful reminder:

- A resource server is not automatically an OAuth client.
- "Public" and "confidential" describe OAuth clients.
- If a component is not acting as a client, "neither" can be the correct answer.

## Part 2 - Separate authentication from API authorization

Answer in your own words.

1. What problem is solved when the employee signs in with Okta?
2. What problem is solved when the React portal receives permission to call the Employee API?
3. What tells the React client about the authenticated employee?
4. What should the React client present to the Employee API?
5. What does the Employee API do with that token at a high level?
6. Does the scheduled Python job need a human user?
7. Does the scheduled Python job need an ID token? Explain why or why not.

## Part 3 - Draw the employee path

Start with these components:

```text
Employee
React Employee Portal
Okta
Employee API
```

Draw the flow and label:

- where user authentication happens
- which component is the client
- which component is the authorization server
- which component is the resource server
- where the ID token is consumed
- where the access token is presented

Do not worry about `/authorize`, `/token`, authorization codes, PKCE, or redirect URIs yet.

Those are taught later.

For Day 1, focus on roles and responsibilities.

## Part 4 - Draw the scheduled-job path

Use:

```text
Scheduled Python Job
Okta
Employee API
```

Label:

- which component is the client
- which component is the authorization server
- which component is the resource server
- whether a human user is present
- which token type is needed for API access

Then explain why an interactive employee login would be the wrong design for this job.

## Part 5 - Find the problem in each statement

For each statement:

1. Say whether it is correct or incorrect.
2. Explain why.

### Statement 1

> We will put the Okta client secret in the React source code.

### Statement 2

> The Employee API should use the ID token as the normal bearer credential because it proves the user logged in.

### Statement 3

> The scheduled Python job should use the same interactive browser sign-in flow as an employee.

### Statement 4

> Once OIDC login works, the user's downstream SaaS account will automatically be created and disabled through the same protocol.

### Statement 5

> If the user successfully signs in to Okta, any later 401 from the Employee API must also be an Okta authentication failure.

## Part 6 - Requirement classification practice

Classify each requirement.

For each one, identify:

```text
Human user involved?
Client?
Resource server?
Authentication needed?
API authorization needed?
Provisioning needed?
Public or confidential client?
```

### Requirement A

A React portal signs employees in and calls a payroll API.

### Requirement B

A server-side Java application only needs employee SSO. It does not call a custom API.

### Requirement C

A nightly Python process sends records to an internal API with no user present.

### Requirement D

A PowerShell process calls Okta Management APIs without a human user.

### Requirement E

A SaaS application needs employee SSO and automatic account creation/deactivation.

Do not worry yet about choosing every exact Okta setting.

First classify the requirement correctly.

## Part 7 - Explain it like you are in a project meeting

Give a short explanation that covers:

```text
What OIDC is doing
What OAuth is doing
Why React is a public client
Why the Python job is different
What the Employee API expects
Why provisioning is separate
```

Try to explain it naturally in less than two minutes.

Do not read definitions.

## Day 1 evidence

There is no live network transaction yet.

For this lab, your evidence is architectural:

- the written requirement
- which component owns each responsibility
- whether a human user is present
- whether the client can protect a credential
- which component consumes each token
- which component hosts the protected resource

## Completion check

You are ready for Day 2 when you can explain all of these without guessing:

- authentication vs authorization
- OAuth vs OIDC
- client
- authorization server
- OpenID Provider
- resource server
- ID token consumer
- access token consumer
- public client
- confidential client
- user-facing flow vs machine-to-machine flow

If any one of these is still unclear, return to the Day 1 lesson before moving forward.
