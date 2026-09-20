# OAuth/OIDC Troubleshooting Symptom Map

Use this only as a starting point. Always confirm the failed step from the actual request, response, token, and Okta System Log.

| Symptom | First areas to investigate |
|---|---|
| Redirect URI error | Requested callback URI vs registered sign-in redirect URI |
| `invalid_client` | Client ID, configured token endpoint auth method, secret/key/assertion |
| `invalid_grant` | Authorization code expiry/reuse, redirect URI equality, PKCE verifier, refresh-token state |
| `invalid_scope` | Requested scope, authorization server, access policy/rule, allowed scope |
| No refresh token returned | `offline_access`, Refresh Token grant enabled, authorization-server policy |
| API returns 401 | Bearer token present? access token vs ID token? Org AS vs Custom AS? signature, issuer, audience, `cid`, expiry, JWKS |
| API returns 403 | Token accepted but required scope/claim/permission missing; inspect granted `scp` before changing token-validation settings |
| Unknown `kid` | Wrong issuer/JWKS, stale key cache, signing-key rotation |
| Audience mismatch | Wrong authorization server, wrong API audience, wrong token sent to API, client/API using different authorization-server boundary |
| Unexpected MFA | Global Session Policy, App Sign-In/Authentication Policy, existing session state; do not start by changing Custom-AS access policy |
| Expected scope missing | Correct Custom AS? Scope defined? Was it requested? Which policy covers the client? Which rule matched first? User/group condition? Did that rule permit the custom scope? |
| Custom access-token claim missing | Claim enabled? correct token type? expression/group filter? user attribute populated? Include-in scope condition? Token Preview vs real flow |
| Login works but OIDC profile claim is missing | Requested OIDC scopes, claim configuration, ID token vs `/userinfo` expectation |
| App logout signs user straight back in | Local application session ended but Okta browser session remains |
| Postman works but SPA fails | CORS, Trusted Origins where applicable, browser cookies, callback handling, PKCE state |
| Wrong token lifetime / specific rule never applies | Access-policy priority, rule priority, earlier broad rule, client/user/group/scope conditions |
| Token Preview works but real flow fails | Redirect URI, assignment, PKCE/callback state, client configuration, real requested scopes, browser/application behavior |
| Works in dev but fails in prod | Issuer, client ID, redirect URI, secret/key, policy, assignment, audience, environment config |
| Token is revoked but API still accepts it | API is probably doing local JWT validation and not checking live revocation state |
| Okta API token obtained but operation denied | OAuth scope may be present while admin role/resource permission is insufficient |

## Investigation order

Ask:

> What is the last step I can prove succeeded?

Then follow the transaction:

```text
1. App builds request
2. Browser reaches /authorize
3. User authentication / policy evaluation
4. Callback / authorization response
5. Authorization code returned
6. Client calls /token
7. Tokens issued
8. Client validates OIDC response / ID token
9. Client calls API with access token
10. API validates access token
11. API authorizes the operation
```

## Evidence rule

When available, use all three:

1. Browser Network tab, curl, or Postman
2. Token inspection
3. Okta System Log

A setting change is not the diagnosis. The diagnosis is the failed step, the evidence showing why it failed, and proof that the corrected configuration changed that behavior.


## Day 10 lifecycle symptoms

| Symptom | First checks |
|---|---|
| Immediate SSO after local logout | Did the app only delete its local session? Is the Okta browser session still active? Did a protected route immediately start /authorize again? |
| Okta logout completed but API token still works | Session logout and token revocation are separate. Check token exp, introspection state, and whether the API uses local JWT validation only. |
| Revoked JWT still returns 200 from local API | Compare /introspect with local validation. A purely local JWT validator has no live revocation state. |
| /revoke returned 200 but token state seems unchanged | 200 does not prove prior token state. Verify the correct token, authorization server, client ID, token type, and introspection result. |
| Refresh works after access-token revocation | Expected if the refresh token was not revoked. Access-token revocation does not revoke its refresh token. |
| Refresh fails after refresh-token rotation | Confirm the client stored the newest refresh token and did not reuse an older rotated value outside the grace behavior. |
| UserInfo profile/email missing | Verify profile/email were granted, correct UserInfo endpoint from discovery, active access token, and which claims the app expects from ID token vs UserInfo. |
| Unexpected logout behavior | Separate local app session, Okta browser session, local token storage, access-token revocation, and refresh-token revocation before changing configuration. |


## Day 11 machine-to-machine symptoms

| Symptom | First checks |
|---|---|
| Client Credentials /token fails before API call | Correct Custom AS? API Services client? client ID/secret? client auth method? service policy assigned to this client? |
| Client authenticates but requested service scope is rejected | Scope exists? service-compatible consent? policy/rule permits scope? rule grant is Client Credentials? user condition is No user? |
| Service rule uses user/group condition | Client Credentials has no user. Use a rule that matches No user rather than inventing a human assignment. |
| Machine token unexpectedly has no user uid | Expected for no-user Client Credentials. Validate the service client using the intended client boundary such as cid, not a human uid requirement. |
| Machine API returns 401 | Bearer token present? issuer, audience, signature, expiry, expected service cid, correct Custom AS token? |
| Machine API returns 403 | Token accepted but required service scope is absent. Compare endpoint requirement with token scp. |
| Service asks for token before every API call | Reuse a still-valid cached token and renew shortly before expiry; do not create needless token traffic. |
| Service retries invalid_client forever | Treat invalid client/configuration as a configuration failure to alert on, not a transient error to retry indefinitely. |
| Browser/CORS/redirect debugging suggested for Client Credentials | Wrong flow. Inspect service HTTP requests, token endpoint response, safe token claims, API response/logs, and Okta evidence. |
| Day 11 request copied to Okta Management APIs | Wrong model. Day 11 protects your own API with a Custom AS and client-secret auth; Okta API service access uses the Org AS and a different authorization model. |


## Day 12 Okta Management API automation symptoms

| Symptom | First checks |
|---|---|
| private_key_jwt token request fails | Org AS /oauth2/v1/token? public/private key auth configured? correct client ID, kid, private key, iss/sub, exact aud, exp, clock, jti replay? |
| Correct key but requested Okta API scope is rejected | Is the scope supported and granted on the service app's Okta API Scopes tab? |
| Token issued with scope but Management API returns authorization error | Scope grant is not admin permission. Check service-app admin role, permission, resource target, or custom role/resource-set binding. |
| Service app works only after Super Admin is assigned | Overprivileged workaround. Determine the actual minimum standard/custom admin role and resource target instead. |
| Automation is using /oauth2/default/v1/token | Wrong authorization server. Okta API scopes for a service app come from the Org Authorization Server /oauth2/v1/token endpoint. |
| Automation uses client_secret_basic for Okta API service access | Wrong client authentication model. Custom OAuth service apps requesting Okta API scopes use private_key_jwt. |
| Assertion aud points to /api/v1/users | Wrong audience. The assertion authenticates to the exact token endpoint, not the downstream Management API endpoint. |
| Org-AS access token is being decoded for authorization logic | Treat the Org-AS token as opaque. Use token response metadata and actual Okta API authorization results. |
| Key rotation causes invalid_client | Verify the new public JWK is registered before deployment, automation uses matching private key/kid, then retire the old key only after successful overlap. |
| Read-only automation has manage scopes | Reduce scope grants and requested scopes to read unless the process actually performs writes. |


## Day 13 browser and authentication symptoms

| Symptom | First checks |
|---|---|
| Browser never leaves the application | JavaScript/runtime error, SDK initialization, local route/click handler, issuer discovery/configuration |
| Browser reaches /authorize but callback never arrives | Actual redirect_uri vs registered redirect URI, client ID/app status, authorization request error |
| Callback reaches app but pending transaction is missing | Transaction cookie/storage, server restart, shared session store, load balancer/node affinity, browser state loss |
| Callback reaches app but state validation fails | Expected state vs returned state; do not move to token/client-secret troubleshooting yet |
| Token exchange succeeds but nonce validation fails | Expected nonce storage, transaction mix-up, OIDC response binding, multiple-tab state |
| User is denied at Okta | Controlled Access/assignment, user status, Global Session Policy, app sign-in policy, authenticator state, System Log |
| Unexpected MFA or reauthentication | Global Session Policy, app sign-in/authentication policy, current Okta session context, authenticator enrollment; do not start with Custom-AS access policy |
| Okta SSO succeeds but application still shows signed out | Local session creation, Set-Cookie, browser cookie storage/send, SPA token/auth state, server session store |
| Local logout is followed immediately by sign-in | Local app session ended but Okta browser session may remain; inspect whether a protected route immediately starts /authorize |
| Postman works but browser fails | CORS/preflight, origin, browser cookies/privacy, storage, mixed content, JavaScript request construction |
| Browser CORS error calling your own API | Configure CORS on your API. An Okta Trusted Origin does not configure your application API |
| Browser CORS error calling Okta | Identify cookie/session vs bearer-token call, endpoint CORS support, and whether Trusted Origin is actually required |
| Dev works but prod fails | Compare issuer, client ID, app type, redirect/sign-out URIs, origins, HTTPS/cookies, policies, Controlled Access, assignments, proxy/session-store behavior |


## Day 14 token, API, refresh, and automation symptoms

| Symptom | First checks |
|---|---|
| Authorization Code /token fails after wrong PKCE verifier | Treat as grant validation. Use a fresh authorization transaction and the matching verifier; do not troubleshoot API scope first. |
| Reused authorization code fails | Expected one-time grant behavior. Start a new authorization request rather than retrying the redeemed code. |
| /token returns invalid_client | Client ID plus configured client-authentication method and credential: secret method, secret value, private key/kid/assertion, or public-client none. |
| Scope request is rejected before token issuance | Correct authorization server? scope exists? policy/rule/grant/user condition? service-app grants collection for Okta API scopes? |
| Custom API returns 401 | Bearer token presence/type, alg/kid/JWKS, signature, issuer, audience, time, expected cid, safe API validation stage. |
| Custom API returns 403 insufficient_scope | Token was trusted. Compare required endpoint scope with granted scp; do not rotate keys or change issuer first. |
| JWT kid not found in cached JWKS | Confirm trusted issuer and discovery, refresh the trusted jwks_uri, then distinguish key rotation/stale cache from wrong issuer/environment or fabricated token. Never disable signature validation. |
| Fresh token appears expired/not-yet-valid | Check host/container/VM clock synchronization before increasing validation leeway. |
| Refresh works after access-token-only revocation | Expected: access-token revocation doesn't revoke its refresh token. Track the current refresh token correctly. |
| Refresh fails after refresh-token revocation | Grant credential is inactive. Resource API is not the first failed layer. |
| Refresh-token reuse detected | Check whether the client stored the newest rotating token, grace period, and System Log reuse-detection event. Do not keep replaying the old token. |
| Day 11 Client Credentials /token succeeds but machine API returns 401 | Resource trust: issuer, audience, signature, expiry, expected service cid, token structure. Client secret already succeeded upstream. |
| Day 11 machine API returns 403 | Resource accepted the token but required service scope is absent. Compare requested/granted/required scope. |
| Day 12 private_key_jwt fails before token issuance | Org AS endpoint, client ID, private key/public JWK, kid, iss/sub, exact aud, exp/iat, jti, and DPoP requirement. |
| Day 12 Okta API scope is rejected | Scope supported? granted to service app? correct Org Authorization Server? read vs manage? |
| Day 12 token contains scope but Management API denies operation | Scope grant isn't admin authorization. Check service-app admin role, permission, resource target, or custom role/resource-set binding. |
| Dev works but prod fails | Compare issuer, AS ID, audience, client ID/auth method, secret/key/kid, policies, scopes, expected cid, JWKS, roles/targets, API base URL, and host clock. |
| Service retries invalid_client forever | Configuration/credential failure, not a transient condition. Stop unbounded retry and alert for correction. |
