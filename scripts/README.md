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

## Added later as the course reaches them

- Client Credentials
- `private_key_jwt`
- Okta OAuth token acquisition
- Okta Management API calls
- JWT inspection/validation exercises

Production integrations should normally use maintained OAuth/OIDC libraries and proper secret/key storage rather than hand-built protocol code.
