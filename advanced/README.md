# Appendix — Advanced OAuth/OIDC (in-scope, for a later pass)

Do **not** study this during the 15 days. It is here so that once the core is second nature — you can design, build, and troubleshoot the five integrations without looking things up — you have a clear path to close the last 10% and gain working knowledge of the less-common OAuth/OIDC patterns that appear in advanced projects (still no SAML or SCIM; those are separate courses).

Everything below is OAuth/OIDC-scoped. Treat each item the same way as the core: understand it, run it, break it, explain it.

## A. DPoP — sender-constrained tokens

**What it is:** Demonstrating Proof-of-Possession. The client holds a key pair and sends a signed **DPoP proof JWT** in a `DPoP` header on each request. The access token is bound to that key (a `cnf`/`jkt` thumbprint), and its type becomes `DPoP`, not `Bearer`.

**Why it matters:** a stolen `Bearer` token is replayable by anyone. A DPoP-bound token is useless without the private key, so it is showing up in higher-security Okta integrations. Okta supports DPoP for API access.

**Day-to-day / troubleshooting angle:**

```text
token_type = DPoP, not Bearer
DPoP proof required on every call (htm = method, htu = URL, iat, jti)
use_dpop_nonce challenge -> retry proof with the returned DPoP-Nonce
clock skew or htu/htm mismatch -> proof rejected
```

**Lab:** enable DPoP on an app, capture the `DPoP` header and the bound access token, then break `htu`, `htm`, and the nonce in turn and read the `401` + `DPoP-Nonce` responses.

## B. Token Exchange (On-Behalf-Of) — delegation in service chains

**What it is:** Okta's On-Behalf-Of (OBO) Token Exchange, `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`. When API1 calls API2 on behalf of a user, API1 **authenticates as the OAuth client** and passes the user's incoming access token as `subject_token`; Okta returns a new token scoped for the downstream API.

**Why it matters:** in a chain (API1 → API2 for a user), you must not forward the original token to the wrong audience. OBO mints a correctly-scoped downstream token that still identifies the original user. Configured on an Okta authorization server.

**The request (OBO shape):**

```text
grant_type   = token-exchange
subject_token = user's incoming access token
subject_token_type = access_token
scope        = downstream (API2) scopes
audience     = downstream authorization-server audience
+ API1 authenticates itself as the OAuth client
```

**The result:**

```text
new access token
  aud = API2's configured Custom Authorization Server audience
  scp = API2 permissions
  sub = original user        (delegation is preserved)
  cid = API1 service client   (which service made the call)
```

Note: Okta's standard OBO example does **not** use an `actor_token` or an `act` claim — use the System Log to see which service acted for which user. (`act` appears in the separate AI-agent / ID-JAG delegation scenario, which is a different use case.)

**Lab:** configure the token-exchange grant, have API1 exchange an incoming user token for a token scoped to API2, then inspect `aud`, `scp`, `sub`, and `cid` before and after.

## C. Consent

**What it is:** a scope can require user or admin **consent**. The user sees a consent prompt; consent can later be granted or revoked; `prompt=consent` forces the screen.

**Why it matters:** an unexpected consent screen — or an API call blocked until consent — is a real ticket, and it is a **different layer** from MFA and from an access-policy denial.

**Day-to-day / troubleshooting angle:** distinguish "blocked by missing consent" from "denied by authorization-server policy" from "authentication/MFA prompt." Each has a different fix and a different System Log signature.

**Lab:** mark a custom scope as requiring consent, trigger the prompt, grant it, then revoke the grant and observe how the next authorization behaves.

## D. Inbound federation and external IdP (OIDC side)

**What it is:** Okta consuming an **external Identity Provider**. Add an external **OIDC** IdP in Okta, route users to it with **IdP routing rules**, and, when required, configure **JIT provisioning/account linking** for federated users.

**Why it matters:** in real organizations, the user often authenticates somewhere else and arrives through Okta. Login problems then have an extra hop: "who actually authenticated this user, and what did Okta receive?" The routing, attribute mapping, and JIT logic are OAuth/OIDC-adjacent and cause real failures.

**Scope note:** an external IdP can also be a **SAML** IdP. The routing/JIT/attribute-mapping concepts are the same, but SAML specifics belong to the SAML course. Here, learn it with an **OIDC** external IdP.

**Day-to-day / troubleshooting angle:**

```text
user -> Okta routing rule -> external OIDC IdP -> back to Okta -> your app
break points: routing rule match, IdP client config, attribute/claim mapping, JIT rules
```

**Lab:** add an external OIDC IdP, create a routing rule, trace a full login through the IdP and back, then break the routing rule and an attribute mapping and diagnose each from the System Log.

## E. Deeper security — attack to defense

The core course teaches the practical security *rules*. On the second pass, connect each defense you already use to the attack it stops, so the design choices stop feeling arbitrary.

| Attack | Defense you already use |
|---|---|
| Authorization-code interception | PKCE (`S256`) |
| Request forgery on the browser flow | `state` |
| ID-token replay | `nonce` |
| Open-redirect abuse | exact registered redirect URIs |
| Token leakage | HTTPS, no tokens in URLs, no token logging |
| Authorization-server mix-up | validate `iss`; distinct redirect URIs per AS |
| Refresh-token exposure/theft | **prevent:** secure storage and minimize exposure. **detect/limit replay:** rotation + reuse detection. **limit impact:** appropriate lifetime |
| Forged/altered token accepted | validate signature, `iss`, `aud`, `exp` — not just "it decodes" |
| Token theft from a SPA (XSS) | **prevent:** XSS/CSP hardening + keep tokens out of browser JS (BFF / HttpOnly cookies). **limit impact only:** short lifetimes + refresh rotation |
| Replay of a stolen bearer token | DPoP (Appendix A) |

**Lab:** for each row, remove or weaken the defense in your lab environment and demonstrate the failure it is meant to prevent. That is the difference between reciting security rules and understanding them.

## How to know you have finished the second pass

You can explain, on a whiteboard, when you would reach for DPoP, Token Exchange, or an external IdP; you can tell a consent denial from a policy denial from an MFA prompt by its System Log signature; and for every parameter in the core flow you can name the attack it defends against. At that point you have working knowledge of the less-common OAuth/OIDC patterns on top of a solid core — the remaining unknowns are product-version details you look up when a project needs them. No engineer is "complete" on every OAuth/OIDC vendor variation, and you do not need to be.

---

# Official Okta references worth bookmarking

Use these as engineering references rather than material to memorize:

- OAuth 2.0 and OpenID Connect overview: https://developer.okta.com/docs/concepts/oauth-openid/
- Authorization servers: https://developer.okta.com/docs/concepts/auth-servers/
- Authorization Code with PKCE: https://developer.okta.com/docs/guides/implement-grant-type/authcodepkce/main/
- Client authentication methods: https://developer.okta.com/docs/api/openapi/okta-oauth/guides/client-auth
- Validate access tokens: https://developer.okta.com/docs/guides/validate-access-tokens/main/
- Refresh tokens: https://developer.okta.com/docs/guides/refresh-tokens/main/
- Configure authorization-server access policies: https://developer.okta.com/docs/guides/configure-access-policy/main/
- Global Session and App Sign-In policies: https://developer.okta.com/docs/guides/configure-signon-policy/main/
- OAuth for Okta API service apps: https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/
- Revoke tokens: https://developer.okta.com/docs/guides/revoke-tokens/main/
- Redirect vs embedded authentication: https://developer.okta.com/docs/concepts/redirect-vs-embedded/

For the advanced appendix (second pass only):

- DPoP: https://developer.okta.com/docs/guides/dpop/
- On-Behalf-Of Token Exchange: https://developer.okta.com/docs/guides/set-up-token-exchange/main/
- External identity providers + IdP Discovery/routing: https://developer.okta.com/docs/concepts/identity-providers/
- Add an external OIDC Identity Provider: https://developer.okta.com/docs/guides/add-an-external-idp/openidconnect/main/
- Custom consent / scopes: https://developer.okta.com/docs/guides/request-user-consent/main/

The point of bookmarking these is not to read every page before you start. Use them when a lab or project gives you a reason to look something up. Okta doc URLs and feature availability change over time, so confirm the current page and whether a feature is enabled in your tenant before relying on it.