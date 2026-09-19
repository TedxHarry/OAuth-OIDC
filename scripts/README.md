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

## Added later as the course reaches them

- Client Credentials
- `private_key_jwt`
- Okta OAuth token acquisition
- Okta Management API calls
- JWT inspection/validation exercises

Production integrations should normally use maintained OAuth/OIDC libraries and proper secret/key storage rather than hand-built protocol code.
