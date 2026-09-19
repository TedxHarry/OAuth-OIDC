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

## Self-check after you finish

Do not read this section until you have attempted the lab.

<details>
<summary>Expected reasoning</summary>

### Part 1

| Component | OAuth/OIDC role | Human user involved in this client flow? | Public, confidential, or neither? | Main responsibility |
|---|---|---|---|---|
| React Employee Portal | Client | Yes | Public | Starts the user-facing flow and calls the API |
| Java Employee API | Resource server | It receives a request made in a user context, but it is not the user-facing OAuth client in this scenario | Neither | Hosts the protected API and evaluates access tokens |
| Scheduled Python Job | Client | No | Confidential | Gets an access token and calls the API as a service |
| Okta | Authorization server and OpenID Provider | It authenticates the user in the employee flow | Neither | Authenticates the user and issues tokens |

The important point is that "public" and "confidential" describe clients. The Employee API is acting as a resource server here.

### Part 2

A strong answer should explain:

- Employee sign-in is an authentication problem.
- Calling the Employee API is an authorization problem.
- The ID token is for the React client.
- The access token is presented to the Employee API.
- The Employee API validates the access token and checks the required permission.
- The scheduled job has no human user and therefore does not need an ID token for user authentication.

### Part 5

1. Incorrect. A browser SPA cannot safely protect a client secret from the user.
2. Incorrect. The ID token is for the client application. The API should normally receive the access token.
3. Incorrect. A scheduled job has no human user available for an interactive sign-in.
4. Incorrect. OIDC does not perform downstream account lifecycle management.
5. Incorrect. Authentication can succeed and the API can still reject the later access-token request.

### Part 6

Requirement A:
- Human user: Yes
- Client: React portal
- Resource server: Payroll API
- Authentication: Yes
- API authorization: Yes
- Client type: Public

Requirement B:
- Human user: Yes
- Client: Server-side Java application
- Authentication: Yes
- Custom API authorization: Not required by the stated requirement
- Client type: Confidential

Requirement C:
- Human user: No
- Client: Nightly Python process
- Resource server: Internal API
- Authentication of a human user: No
- API authorization: Yes
- Client type: Confidential

Requirement D:
- Human user: Yes for SSO
- Authentication: Yes
- Provisioning: Yes
- Important conclusion: SSO and provisioning are separate requirements

</details>

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
