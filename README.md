# OAuth & OIDC for Okta Implementation Engineers

This repository is a practical 15-day course for learning OAuth 2.0 and OpenID Connect in the way an Okta implementation engineer uses them at work.

## Who this course is for

This course assumes the learner is new to OAuth/OIDC.

The learner does not need prior OAuth/OIDC knowledge. Each topic must be taught before the learner is asked to configure, test, or troubleshoot it.

The goal is not to rush through 15 days. The goal is to learn, understand, practice where useful, and become comfortable enough to reason through a real implementation without depending on memorized steps.

The course should build knowledge in this order:

1. Start with a real requirement.
2. Explain the problem that needs to be solved.
3. Teach the concept in plain language.
4. Explain why the concept exists.
5. Draw the architecture or transaction.
6. Show what each component does.
7. Walk through one successful example.
8. Use hands-on work when it helps make the concept clear.
9. Break something only after the successful behavior is understood.
10. Troubleshoot from evidence.
11. Ask the learner to explain the result in their own words.

A lab must not introduce important concepts that the lesson has not already explained.

The focus is on:

- understanding the logic behind each flow and configuration
- seeing what happens in the browser, application, Okta, and API
- implementing real integrations
- reading the actual HTTP requests, responses, cookies, and tokens
- protecting APIs
- building machine-to-machine and Okta API automation
- troubleshooting from evidence instead of changing settings at random
- explaining root causes clearly to application owners and developers

The course intentionally avoids protocol history, RFC memorization, cryptographic mathematics, and uncommon extensions until a project actually requires them.

## How to study

Each lesson follows the same engineering cycle:

1. Understand why the feature exists.
2. Draw who communicates with whom.
3. Trace the frontend and backend behavior.
4. Inspect the real HTTP transaction.
5. Configure the Okta side.
6. Configure or understand the application/API side.
7. Run the integration.
8. Break one thing deliberately.
9. Prove the failure using evidence.
10. Fix it and prove why the fix worked.
11. Explain the root cause in plain language.

For troubleshooting, use three sources whenever possible:

- Browser Network tab, curl, or Postman
- token inspection
- Okta System Log

Do not accept "I changed this setting and it worked" as a diagnosis.

## Source of truth

The **split files are the authoritative working course**:

- `lessons/` for the day-by-day teaching material
- `diagrams/` for reusable architecture and transaction flows
- `labs/` for hands-on and break/fix exercises
- `troubleshooting/` for reusable investigation guides
- `reference/` for the execution plan and checklists
- `advanced/` for the second-pass topics

`reference/master-course.md` is a **consolidated snapshot/reference copy**. Do not edit it as the primary source. When course content changes, update the split file first. This avoids maintaining two independent copies of the same lesson.

## Start here

1. [Open the Day 1–15 lesson index](lessons/README.md)
2. [Use the 15-day execution plan](reference/15-day-plan.md)
3. [Keep the project intake checklist for real integrations](reference/project-intake-checklist.md)
4. [Use the engineer confidence checklist to measure progress](reference/engineer-confidence-checklist.md)
5. [Use the consolidated master snapshot only as a reference copy](reference/master-course.md)

The `advanced/` material is a second pass. Do not study it during the core 15 days.

## Course structure

- `lessons/` - the actual day-by-day teaching material
- `diagrams/` - Mermaid architecture and transaction flows
- `labs/` - hands-on exercises and break/fix work
- `troubleshooting/` - reusable investigation guides
- `reference/` - curriculum, checklists, and project intake material
- `scripts/` - Python and PowerShell examples used in automation labs
- `advanced/` - second-pass topics only after the 15-day core is comfortable

## 15-day path

| Day | Focus |
|---|---|
| 1 | Core OAuth/OIDC logic and application architecture |
| 2 | HTTP, redirects, cookies, headers, and transaction tracing |
| 3 | Authorization Code + PKCE |
| 4 | ID, access, and refresh tokens |
| 5 | JWT validation, discovery, and JWKS |
| 6 | Okta application configuration and client authentication |
| 7 | Server-side web app and SPA integrations |
| 8 | Protecting an API |
| 9 | Authorization servers, scopes, claims, audience, and policies |
| 10 | Sessions, logout, UserInfo, refresh, revocation, and introspection |
| 11 | Client Credentials and machine-to-machine integration |
| 12 | Okta Management API automation |
| 13 | Browser and authentication troubleshooting |
| 14 | Token, API, and automation troubleshooting |
| 15 | End-to-end implementation capstone |

## Target

At the end of the course, you should be able to take a real application requirement, choose the right OAuth/OIDC design, configure Okta, work with the application/API team, implement or guide the integration, test it, and troubleshoot the common failures independently.

The aim is not to know every OAuth feature. The aim is to handle the common day-to-day implementation and support work confidently and know how to investigate the uncommon cases when they appear.
