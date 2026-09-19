#!/usr/bin/env python3
"""Prepare a Day 3 Authorization Code with PKCE transaction.

Example:
    python scripts/python/day03_prepare_authorization.py \
      --okta-domain https://integrator-123456.okta.com \
      --client-id 0oa...

The script prints:
    state
    nonce
    code_verifier
    code_challenge
    authorization URL

Keep the code_verifier in your terminal. Do not send it in the /authorize
request. You need it later for the /token request.
"""

import argparse
import base64
import hashlib
import secrets
from urllib.parse import urlencode


DEFAULT_REDIRECT_URI = "http://localhost:8000/callback"
DEFAULT_SCOPE = "openid profile email"


def base64url_no_padding(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce_values():
    verifier = secrets.token_urlsafe(64)
    challenge = base64url_no_padding(
        hashlib.sha256(verifier.encode("ascii")).digest()
    )
    return verifier, challenge


def normalize_domain(domain: str) -> str:
    value = domain.strip().rstrip("/")
    if not value.startswith("https://"):
        raise ValueError(
            "Use the full HTTPS Okta domain, for example "
            "https://integrator-123456.okta.com"
        )
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--okta-domain", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    args = parser.parse_args()

    okta_domain = normalize_domain(args.okta_domain)
    verifier, challenge = create_pkce_values()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    params = {
        "client_id": args.client_id,
        "response_type": "code",
        "scope": args.scope,
        "redirect_uri": args.redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    authorize_url = (
        f"{okta_domain}/oauth2/v1/authorize?"
        f"{urlencode(params)}"
    )

    print("\nDAY 3 TRANSACTION VALUES")
    print("========================")
    print(f"state={state}")
    print(f"nonce={nonce}")
    print(f"code_verifier={verifier}")
    print(f"code_challenge={challenge}")
    print("code_challenge_method=S256")

    print("\nAUTHORIZATION URL")
    print("=================")
    print(authorize_url)

    print("\nTOKEN ENDPOINT")
    print("==============")
    print(f"{okta_domain}/oauth2/v1/token")

    print("\nKEEP THIS TERMINAL OPEN")
    print("=======================")
    print("You need the state and code_verifier later in the lab.")


if __name__ == "__main__":
    main()
