# Day 1 Lab — Read the Requirement Before Choosing a Flow

## Scenario

A company has:

- a React employee portal
- a Java Employee API
- Okta for workforce authentication
- a scheduled backend job that also calls the Employee API

The application owner says:

> We need OAuth login, secure API access, and the scheduled job should work without a user signing in.

## Your job

Do not configure anything yet.

First identify each component and the problem it needs OAuth/OIDC to solve.

## Step 1 — Classify the components

Fill this in before looking at the answer:

| Component | User present? | Public or confidential? | Main job |
|---|---:|---|---|
| React portal |  |  |  |
| Java API |  |  |  |
| Scheduled job |  |  |  |
| Okta |  |  |  |

## Step 2 — Separate authentication from API authorization

Answer:

1. What proves the employee signed in?
2. What authorizes the React application to call the Employee API?
3. What authorizes the scheduled job when no human user is present?
4. Which component should consume the ID token?
5. Which component should consume the access token?

## Step 3 — Draw the two paths

### Employee path

Draw:

```text
Employee
   |
   v
React
   |
   v
Okta
   |
   v
React
   |
   v
Employee API
```

Label where authentication happens and where API authorization happens.

### Scheduled-job path

Draw:

```text
Scheduled job
     |
     v
Okta
     |
     v
Employee API
```

Explain why there is no browser login and no ID token in this path.

## Step 4 — Explain the design in plain language

Give a short explanation you could use with an application owner:

- OIDC handles ...
- OAuth handles ...
- the React application is ...
- the scheduled job is ...
- the API trusts ...

Keep it under one minute.

## Break/fix questions

For each statement, explain what is wrong:

1. "We will put the client secret in the React source code."
2. "The API can accept the ID token because it proves the user signed in."
3. "The scheduled job can use the same browser login flow."
4. "OIDC will also create and disable the user's downstream account."

## Evidence habit

There is no live transaction yet, so Day 1 evidence is architectural:

- requirement
- component ownership
- whether a user is present
- where credentials can be protected
- which component consumes each token

Do not choose a grant type until those facts are clear.

## Completion check

You are done when you can look at a new application diagram and identify:

- client
- authorization server
- resource server/API
- user
- authentication requirement
- API authorization requirement
- public vs confidential client
- whether a human user is involved
