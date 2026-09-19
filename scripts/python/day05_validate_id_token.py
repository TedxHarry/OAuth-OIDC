#!/usr/bin/env python3
"""Validate an Okta ID token for the Day 5 lab.

Dependency:
    python -m pip install "PyJWT[crypto]"

Example:
    python scripts/python/day05_validate_id_token.py --issuer https://integrator-123456.okta.com --client-id 0oa... --nonce EXPECTED_NONCE

The token is requested interactively with hidden input.
"""

import argparse
import getpass
import json
import urllib.request

import jwt
from jwt import PyJWKClient


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def normalize_issuer(value):
    return value.strip().rstrip("/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--nonce")
    parser.add_argument("--leeway", type=int, default=60)
    args = parser.parse_args()

    issuer = normalize_issuer(args.issuer)
    discovery_url = f"{issuer}/.well-known/openid-configuration"

    print("Fetching OIDC discovery metadata from:")
    print(discovery_url)

    metadata = fetch_json(discovery_url)

    discovered_issuer = metadata.get("issuer")
    jwks_uri = metadata.get("jwks_uri")

    if discovered_issuer != issuer:
        raise SystemExit(
            "Discovery issuer mismatch. "
            f"Expected {issuer!r}, got {discovered_issuer!r}."
        )

    if not jwks_uri:
        raise SystemExit("Discovery document did not contain jwks_uri.")

    print("\nTrusted discovery values")
    print("========================")
    print(f"issuer={discovered_issuer}")
    print(f"jwks_uri={jwks_uri}")

    token = getpass.getpass("\nPaste ID token (input hidden): ").strip()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise SystemExit(f"Unable to parse JWT header: {exc}") from exc

    print("\nUnverified header")
    print("=================")
    print(json.dumps(header, indent=2, sort_keys=True))

    algorithm = header.get("alg")
    key_id = header.get("kid")

    if algorithm != "RS256":
        raise SystemExit(
            f"Rejected: expected alg='RS256', got {algorithm!r}."
        )

    if not key_id:
        raise SystemExit("Rejected: token header has no kid.")

    print(f"\nSelecting public signing key for kid={key_id}")

    try:
        jwk_client = PyJWKClient(jwks_uri)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
    except Exception as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: JWKS key resolution\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=args.client_id,
            issuer=issuer,
            leeway=args.leeway,
            options={
                "require": ["iss", "sub", "aud", "iat", "exp"],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: expiration check\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: audience check\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.InvalidIssuerError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: issuer check\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.InvalidSignatureError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: signature verification\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.ImmatureSignatureError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: time claim check\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.MissingRequiredClaimError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: required-claim check\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc
    except jwt.PyJWTError as exc:
        raise SystemExit(
            "ID TOKEN VALIDATION FAILED\n"
            "Stage: JWT signature or claim validation\n"
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if args.nonce is not None:
        actual_nonce = claims.get("nonce")
        if actual_nonce != args.nonce:
            raise SystemExit(
                "ID TOKEN VALIDATION FAILED\n"
                "Stage: nonce check\n"
                "Nonce mismatch: returned nonce does not equal expected nonce."
            )

    print("\nID TOKEN VALIDATION PASSED")
    print("==========================")
    print("Signature: valid")
    print("Algorithm: RS256")
    print(f"kid: {key_id}")
    print(f"iss: {claims.get('iss')}")
    print(f"aud: {claims.get('aud')}")
    print(f"sub: {claims.get('sub')}")
    print(f"iat: {claims.get('iat')}")
    print(f"exp: {claims.get('exp')}")

    if args.nonce is not None:
        print("nonce: matched expected value")


if __name__ == "__main__":
    main()
