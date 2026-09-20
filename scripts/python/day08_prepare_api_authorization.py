#!/usr/bin/env python3
"""Prepare a Day 8 Authorization Code + PKCE request for a Custom Authorization Server.

Example:
    python scripts/python/day08_prepare_api_authorization.py \
      --issuer https://integrator-123456.okta.com/oauth2/default \
      --client-id 0oa... \
      --scope "openid employee.read"

The script uses OIDC discovery from the configured issuer so it works with the
Custom Authorization Server endpoints rather than assuming the Org Authorization
Server paths used in Day 3.

Keep the generated code_verifier and state private on your machine.
"""

import argparse
import base64
import hashlib
import json
import secrets
import urllib.request
from urllib.parse import urlencode


DEFAULT_REDIRECT_URI = "http://localhost:8000/callback"
DEFAULT_SCOPE = "openid employee.read"


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def normalize_issuer(value):
    return value.strip().rstrip("/")


def base64url_no_padding(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce_pair():
    verifier = secrets.token_urlsafe(64)

    if not 43 <= len(verifier) <= 128:
        raise RuntimeError(
            "Generated PKCE verifier length is outside the RFC 7636 range."
        )

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64url_no_padding(digest)
    return verifier, challenge


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    args = parser.parse_args()

    issuer = normalize_issuer(args.issuer)
    discovery_url = issuer + "/.well-known/openid-configuration"

    metadata = fetch_json(discovery_url)

    if metadata.get("issuer") != issuer:
        raise SystemExit(
            "Discovery issuer mismatch. "
            "Expected %r, got %r."
            % (issuer, metadata.get("issuer"))
        )

    authorize_endpoint = metadata.get("authorization_endpoint")
    token_endpoint = metadata.get("token_endpoint")

    if not authorize_endpoint or not token_endpoint:
        raise SystemExit(
            "Discovery metadata is missing authorization_endpoint or token_endpoint."
        )

    verifier, challenge = create_pkce_pair()
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

    authorize_url = authorize_endpoint + "?" + urlencode(params)

    print("")
    print("DAY 8 CUSTOM AUTHORIZATION SERVER TRANSACTION")
    print("=============================================")
    print("issuer=%s" % issuer)
    print("scope=%s" % args.scope)
    print("state=%s" % state)
    print("nonce=%s" % nonce)
    print("code_verifier=%s" % verifier)
    print("code_challenge=%s" % challenge)
    print("code_challenge_method=S256")

    print("")
    print("AUTHORIZATION URL")
    print("=================")
    print(authorize_url)

    print("")
    print("TOKEN ENDPOINT")
    print("==============")
    print(token_endpoint)

    print("")
    print("KEEP THIS TERMINAL OPEN")
    print("=======================")
    print("You need the state and code_verifier for this transaction.")
    print("Do not commit or share the verifier or resulting tokens.")


if __name__ == "__main__":
    main()
