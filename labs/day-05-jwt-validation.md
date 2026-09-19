# Day 5 Lab - Validate a Real Okta ID Token

## Purpose

Day 4 decoded an ID token.

Day 5 proves whether it can be trusted.

You will validate a real Okta ID token using:

- expected issuer
- OIDC discovery
- JWKS
- kid
- RS256 signature
- audience
- expiration
- nonce

Then you will break individual parts and identify exactly which validation fails.

Complete the lesson first:

[Day 5 - JWT Validation, Discovery, and JWKS](../lessons/day-05-jwt-validation.md)

## Safety rule

Do not commit a live ID token to GitHub.

Do not paste it into chat or public decoder websites.

The course scripts accept the token using hidden terminal input.

## Part 1 - Create a Python virtual environment

From the repository root:

~~~powershell
python -m venv .venv
~~~

On Windows PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
~~~

Install:

~~~powershell
python -m pip install "PyJWT[crypto]"
~~~

The cryptographic work is handled by maintained libraries.

We are learning validation logic, not implementing RSA ourselves.

## Part 2 - Obtain a fresh ID token

Use the Day 4 Authorization Code + PKCE flow.

Keep locally:

~~~text
Okta org domain
SPA client ID
expected nonce
ID token
~~~

For this lab, expected issuer is:

~~~text
https://YOUR-OKTA-DOMAIN
~~~

because we are still using the org authorization server.

## Part 3 - Inspect discovery

Open:

~~~text
https://YOUR-OKTA-DOMAIN/.well-known/openid-configuration
~~~

Find:

~~~text
issuer
authorization_endpoint
token_endpoint
jwks_uri
~~~

Record the values.

Answer:

1. Does issuer equal the issuer configured for the lab?
2. Does authorization_endpoint match Day 3?
3. Does token_endpoint match Day 3?
4. What is jwks_uri?

## Part 4 - Open the JWKS

Open the jwks_uri from the discovery document.

You should see a keys array.

Fields can include:

~~~text
kid
kty
use
alg
n
e
~~~

Find the kid values.

## Part 5 - Inspect the ID token header

Run:

~~~powershell
python scripts/python/day04_decode_id_token.py
~~~

Find:

~~~text
alg
kid
~~~

Compare the token kid with the JWKS.

Can you find the matching public key?

## Part 6 - Validate the real ID token

Run this on one line:

~~~powershell
python scripts/python/day05_validate_id_token.py --issuer https://YOUR-OKTA-DOMAIN --client-id YOUR-CLIENT-ID --nonce YOUR-EXPECTED-NONCE
~~~

Paste the ID token when prompted.

Expected result:

~~~text
ID TOKEN VALIDATION PASSED
~~~

The script validates:

~~~text
expected algorithm
signature
issuer
audience
required claims
expiration/time behavior
nonce, when supplied
~~~

It obtains jwks_uri from trusted discovery metadata.

## Part 7 - Trace the trust chain

Write this using your real values:

~~~text
Expected issuer:
Discovery URL:
Discovered issuer:
JWKS URI:
Token alg:
Token kid:
Matching key found?:
Expected audience:
Token audience:
Expected nonce:
Token nonce matched?:
Validation result:
~~~

This is stronger evidence than saying the token looked right.

## Part 8 - Break audience validation

Run the validator again with an intentionally wrong client ID.

Example:

~~~text
--client-id not-the-real-client-id
~~~

Keep issuer, token, and nonce correct.

Record the validation failure.

Explain:

> Why can a correctly signed ID token still be rejected when aud is wrong?

## Part 9 - Break nonce validation

Run the validator with:

~~~text
--nonce wrong-nonce-for-day5
~~~

Keep the real issuer and client ID.

The signature and core claims can validate, but the final nonce comparison should fail.

Record:

~~~text
signature stage:
issuer:
audience:
nonce:
final result:
~~~

Explain why this differs from a bad signature.

## Part 10 - Modify the payload without resigning

Run:

~~~powershell
python scripts/python/day05_tamper_jwt.py --mode payload
~~~

Paste your valid ID token.

The script adds:

~~~text
day5_tampered=true
~~~

to the payload but keeps the original signature.

Copy the resulting intentionally invalid JWT.

Run the normal validator against it.

Expected:

~~~text
signature validation failure
~~~

Explain:

~~~text
Claims are readable.
JWT structure is valid.
Signed content changed.
Original signature no longer matches.
~~~

This is why decoding alone is not validation.

## Part 11 - Simulate unknown kid

Run:

~~~powershell
python scripts/python/day05_tamper_jwt.py --mode kid
~~~

The script changes the header kid to:

~~~text
day5-unknown-kid
~~~

without creating a new signature.

Validate that token.

The validator should not find a trusted signing key for that kid and should reject the token.

Record the actual error.

Production logic:

~~~text
kid missing from cached JWKS
        |
        v
refresh JWKS from trusted jwks_uri
        |
        v
kid still missing?
        |
        +-- yes -> reject
        |
        +-- no -> continue signature validation
~~~

## Part 12 - Do not bypass unknown kid

Answer:

> Why is choosing another key from JWKS not a valid fix?

The kid identifies the key corresponding to the signing key.

An unrelated key does not make the signature valid.

## Part 13 - Explain a wrong issuer

You do not need to point the script at an untrusted server.

Explain:

~~~text
Configured issuer:
https://company.okta.com

Token iss:
https://other-company.okta.com
~~~

Even if the other company signed its token correctly, your client rejects it because it trusts the configured issuer.

## Part 14 - Validation vs authorization

Answer:

> If the ID token validates successfully, does that mean the employee is allowed to approve payroll?

No.

Validation establishes trust in the authentication token.

Payroll approval is a separate authorization decision.

## Part 15 - Evidence record

Record:

~~~text
Configured issuer:
Discovery URL:
jwks_uri:
Token alg:
Token kid:
Matching public key found?:

Valid token:
signature:
iss:
aud:
exp:
nonce:
result:

Wrong audience test:
result:
failure:

Wrong nonce test:
result:
failure:

Tampered payload test:
result:
failure:

Unknown kid test:
result:
failure:
~~~

Do not store token strings.

## Self-check after you finish

<details>
<summary>Expected reasoning</summary>

### Decode vs validate

Decoding only makes header and payload readable.

Validation establishes trust.

### Discovery

The application begins with an expected trusted issuer and obtains metadata from that issuer.

### JWKS

JWKS publishes public signing keys.

### kid

kid selects the public key corresponding to the signing key.

### Signature

Changing the signed header or payload without a new valid signature causes validation to fail.

### Audience

A signed token for another client is not your ID token.

### Nonce

A validly signed token can still fail the transaction-specific nonce check.

### Unknown kid

Refresh trusted JWKS when appropriate. If the key still cannot be resolved, reject.

</details>

## Day 5 completion check

You are ready for Day 6 when you can explain:

~~~text
Why decode is not validation
Where discovery comes from
What jwks_uri provides
How kid selects a key
What signature validation proves
Why iss must match
Why aud must match
Why exp matters
Why nonce matters
How key rotation affects validation
Why validation and authorization are separate
~~~
