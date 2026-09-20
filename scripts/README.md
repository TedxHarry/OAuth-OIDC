# Scripts

Small Python and PowerShell examples used during the course.

## Available now

### Day 2 HTTP lab

- [Python - local HTTP lab server](python/day02_http_lab_server.py)

### Day 3 Authorization Code with PKCE

- [Python - prepare authorization values and URL](python/day03_prepare_authorization.py)
- [Python - local PKCE callback receiver](python/day03_pkce_callback_server.py)
- [Python - generate only a PKCE verifier and S256 challenge](python/generate_pkce_pair.py)
- [PowerShell - generate PKCE verifier and S256 challenge](powershell/Generate-PkcePair.ps1)

These are useful for Day 3 when you want to see the verifier/challenge relationship directly instead of relying only on an SDK.

### Day 4 token inspection

- [Python - decode an ID token for inspection only](python/day04_decode_id_token.py)

The Day 4 decoder does not validate the token. Day 5 adds validation.

### Day 5 JWT validation

- [Python - validate an Okta ID token](python/day05_validate_id_token.py)
- [Python - create intentionally invalid JWTs for break/fix](python/day05_tamper_jwt.py)

Dependency for the validator: `PyJWT[crypto]`.

### Day 7 application architecture

- [Python - server-side Web Application](python/day07_web_app.py)
- [Browser SPA - Okta Auth JS + Vite](day07_spa/)

The Web Application keeps OAuth transaction data and tokens server-side and gives the browser an opaque HttpOnly application-session cookie. The SPA uses Okta Auth JS and stores tokens in browser `sessionStorage` for the lab so the trust-boundary difference is visible.

### Day 8 protected API

- [Python - prepare Custom Authorization Server authorization](python/day08_prepare_api_authorization.py)
- [Python - inspect access-token claims without validation](python/day08_inspect_access_token.py)
- [Python - protected Employee API](python/day08_employee_api.py)

The Day 8 API validates Custom Authorization Server access tokens, then enforces `employee.read`. It returns 401 for missing/invalid bearer credentials and 403 for a trusted token with insufficient scope.

### Day 9 authorization design

- [Python - inspect Day 9 custom claims and token lifetime](python/day09_inspect_access_token.py)
- [Python - Employee API with employee.read and salary.read](python/day09_employee_api.py)

Day 9 reuses the Day 8 Custom Authorization Server authorization helper because that helper accepts any trusted Custom Authorization Server issuer. The Day 9 API enforces scopes only; `department` and filtered `groups` are returned as context and are not hidden extra authorization checks.

### Day 10 session and token lifecycle

- [Python - server-side local vs Okta session logout app](python/day10_session_app.py)
- [Python - public-client UserInfo, introspection, and revocation utility](python/day10_lifecycle_client.py)

Day 10 reuses the Day 9 API to demonstrate that a revoked but unexpired JWT can still satisfy purely local JWT validation while Okta introspection reports it inactive.

### Day 11 Client Credentials

- [Python - machine-to-machine Employee API endpoint](python/day11_employee_api.py)
- [Python - Client Credentials reporting service](python/day11_service_client.py)

The Day 11 service client uses an API Services client with `client_secret_basic` against the Employee API Custom Authorization Server. It keeps the bearer token only in process memory and reuses it until near expiry. The Day 11 API expects the service `cid` and `employee.report.read`; it does not require a human user `uid`.

### Day 12 Okta Management API automation

- [Python - generate a local RSA signing key pair](python/day12_generate_keypair.py)
- [Python - private_key_jwt Okta Management API client](python/day12_okta_api_client.py)

Day 12 uses the Org Authorization Server and `private_key_jwt`. The private key stays under the ignored local `secrets/` directory; only the public JWK is registered with Okta. The automation client never prints or decodes the Org-AS access token.

### Day 13 browser and authentication troubleshooting

- [Python - blind browser/OIDC fault harness](python/day13_web_faults.py)
- [Python - local two-origin CORS evidence lab](python/day13_cors_lab.py)

The Day 13 Web harness hides five fault causes behind Case A-E so the learner must diagnose from Browser Network, application stage logs, and Okta evidence before opening the answer key. The CORS helper demonstrates that a browser can fail at preflight while the same API succeeds from curl or Postman.

Production integrations should normally use maintained OAuth/OIDC libraries and proper secret/key storage rather than hand-built protocol code.
