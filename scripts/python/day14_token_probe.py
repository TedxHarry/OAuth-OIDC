#!/usr/bin/env python3
"""Day 14 safe Custom Authorization Server token probe.

Use this only for JWT access tokens intended for APIs that you own and validate.

Do NOT use this helper to build authorization logic from an Okta Org
Authorization Server access token. Day 12 treats Org-AS access tokens as opaque.

Dependencies:
    python -m pip install requests "PyJWT[crypto]"

Environment variables for validation:
    DAY14_EXPECTED_ISSUER
    DAY14_EXPECTED_AUDIENCE
    DAY14_EXPECTED_CLIENT_ID   optional

Examples:
    python scripts/python/day14_token_probe.py --action inspect
    python scripts/python/day14_token_probe.py --action jwks
    python scripts/python/day14_token_probe.py --action validate
    python scripts/python/day14_token_probe.py --action call-api \
      --api-url http://localhost:7000/api/employees

Controlled API faults:
    --fault malformed
    --fault unknown-kid
    --fault signature

Security:
- The bearer token is entered through a hidden prompt.
- The raw token is never printed.
- Only selected troubleshooting metadata is printed.
"""

import argparse
import base64
import getpass
import json
import os
import time

import jwt
import requests
from jwt import PyJWKClient


EXPECTED_ISSUER = os.environ.get("DAY14_EXPECTED_ISSUER", "").rstrip("/")
EXPECTED_AUDIENCE = os.environ.get("DAY14_EXPECTED_AUDIENCE", "")
EXPECTED_CLIENT_ID = os.environ.get("DAY14_EXPECTED_CLIENT_ID", "")


def b64url_decode_json(segment):
    padding = "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(segment + padding)
    return json.loads(raw.decode("utf-8"))


def b64url_encode_json(value):
    raw = json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def read_token():
    token = getpass.getpass("Paste token locally (input hidden): ").strip()

    if not token:
        raise SystemExit("No token was supplied.")

    return token


def parse_unverified(token):
    parts = token.split(".")

    if len(parts) != 3:
        raise ValueError("Token does not have three JWT segments.")

    header = b64url_decode_json(parts[0])
    payload = b64url_decode_json(parts[1])
    return header, payload


def safe_summary(header, payload):
    now = int(time.time())
    exp = payload.get("exp")
    iat = payload.get("iat")

    summary = {
        "alg": header.get("alg"),
        "kid": header.get("kid"),
        "typ": header.get("typ"),
        "iss": payload.get("iss"),
        "aud": payload.get("aud"),
        "cid": payload.get("cid"),
        "scp": payload.get("scp"),
        "iat": iat,
        "exp": exp,
        "sub_present": "sub" in payload,
        "uid_present": "uid" in payload,
        "seconds_until_exp": (
            exp - now if isinstance(exp, int) else None
        ),
        "raw_token_printed": False,
        "signature_validated_by_inspection": False,
    }

    return summary


def apply_fault(token, fault):
    if fault == "none":
        return token

    if fault == "malformed":
        return "not-a-jwt"

    parts = token.split(".")

    if len(parts) != 3:
        raise SystemExit(
            "The supplied token must be a JWT before a JWT fault can be applied."
        )

    if fault == "unknown-kid":
        header = b64url_decode_json(parts[0])
        header["kid"] = "day14-not-a-real-kid"
        parts[0] = b64url_encode_json(header)
        return ".".join(parts)

    if fault == "signature":
        signature = parts[2]

        if not signature:
            raise SystemExit("JWT signature segment is empty.")

        padding = "=" * (-len(signature) % 4)
        raw = bytearray(base64.urlsafe_b64decode(signature + padding))

        if not raw:
            raise SystemExit("JWT signature decoded to an empty value.")

        raw[0] ^= 0x01
        parts[2] = base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode("ascii")
        return ".".join(parts)

    raise SystemExit("Unsupported fault: %s" % fault)


def require_expected_issuer():
    if not EXPECTED_ISSUER:
        raise SystemExit(
            "Set DAY14_EXPECTED_ISSUER for this action."
        )


def fetch_discovery():
    require_expected_issuer()

    url = EXPECTED_ISSUER + "/.well-known/openid-configuration"
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    metadata = response.json()

    if metadata.get("issuer") != EXPECTED_ISSUER:
        raise RuntimeError(
            "Discovery issuer mismatch. Expected %r, got %r."
            % (EXPECTED_ISSUER, metadata.get("issuer"))
        )

    jwks_uri = metadata.get("jwks_uri")

    if not jwks_uri:
        raise RuntimeError("Discovery metadata did not contain jwks_uri.")

    return metadata


def action_inspect(token):
    try:
        header, payload = parse_unverified(token)
    except Exception as exc:
        print("inspection_result=failed")
        print("stage=jwt_structure")
        print("detail=%s" % type(exc).__name__)
        return

    print(json.dumps(
        safe_summary(header, payload),
        indent=2,
        sort_keys=True,
    ))


def action_jwks(token):
    try:
        header, payload = parse_unverified(token)
    except Exception as exc:
        print("jwks_check=failed")
        print("stage=jwt_structure")
        print("detail=%s" % type(exc).__name__)
        return

    metadata = fetch_discovery()
    jwks_uri = metadata["jwks_uri"]

    response = requests.get(
        jwks_uri,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    keys = response.json().get("keys", [])

    kid = header.get("kid")
    matching = [key for key in keys if key.get("kid") == kid]

    result = {
        "expected_issuer": EXPECTED_ISSUER,
        "token_iss": payload.get("iss"),
        "jwks_uri": jwks_uri,
        "token_kid": kid,
        "jwks_key_count": len(keys),
        "kid_in_current_jwks": bool(matching),
        "raw_token_printed": False,
    }

    print(json.dumps(result, indent=2, sort_keys=True))


def action_validate(token):
    require_expected_issuer()

    if not EXPECTED_AUDIENCE:
        raise SystemExit(
            "Set DAY14_EXPECTED_AUDIENCE for validation."
        )

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        print("validation=failed")
        print("stage=jwt_header")
        print("detail=%s" % type(exc).__name__)
        return

    if header.get("alg") != "RS256":
        print("validation=failed")
        print("stage=algorithm")
        print("detail=expected_RS256")
        return

    if not header.get("kid"):
        print("validation=failed")
        print("stage=kid")
        print("detail=missing_kid")
        return

    metadata = fetch_discovery()
    jwks_uri = metadata["jwks_uri"]

    try:
        signing_key = PyJWKClient(jwks_uri).get_signing_key_from_jwt(token)
    except Exception as exc:
        print("validation=failed")
        print("stage=jwks_key_resolution")
        print("detail=%s" % type(exc).__name__)
        return

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=EXPECTED_AUDIENCE,
            issuer=EXPECTED_ISSUER,
            leeway=60,
            options={
                "require": [
                    "iss",
                    "aud",
                    "iat",
                    "exp",
                    "cid",
                    "scp",
                ],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        stage = "expiration"
        detail = type(exc).__name__
    except jwt.InvalidAudienceError as exc:
        stage = "audience"
        detail = type(exc).__name__
    except jwt.InvalidIssuerError as exc:
        stage = "issuer"
        detail = type(exc).__name__
    except jwt.InvalidSignatureError as exc:
        stage = "signature"
        detail = type(exc).__name__
    except jwt.ImmatureSignatureError as exc:
        stage = "time_claim"
        detail = type(exc).__name__
    except jwt.MissingRequiredClaimError as exc:
        stage = "required_claim"
        detail = str(exc.claim)
    except jwt.PyJWTError as exc:
        stage = "jwt_validation"
        detail = type(exc).__name__
    else:
        if EXPECTED_CLIENT_ID and claims.get("cid") != EXPECTED_CLIENT_ID:
            print("validation=failed")
            print("stage=client_id")
            print("detail=unexpected_cid")
            return

        scopes = claims.get("scp")

        if not isinstance(scopes, list):
            print("validation=failed")
            print("stage=scope_claim")
            print("detail=scp_not_list")
            return

        print("validation=passed")
        print("issuer=%s" % claims.get("iss"))
        print("audience=%s" % claims.get("aud"))
        print("client_id=%s" % claims.get("cid"))
        print("scopes=%s" % scopes)
        print("raw_token_printed=False")
        return

    print("validation=failed")
    print("stage=%s" % stage)
    print("detail=%s" % detail)


def action_call_api(token, api_url):
    if not api_url:
        raise SystemExit("--api-url is required for call-api.")

    response = requests.get(
        api_url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
        },
        timeout=15,
    )

    print("api_http=%s" % response.status_code)
    print(
        "www_authenticate=%s"
        % response.headers.get("WWW-Authenticate")
    )
    print(
        "x_correlation_id=%s"
        % response.headers.get("X-Correlation-ID")
    )

    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        safe = {
            key: body.get(key)
            for key in ("error", "message", "correlation_id")
            if key in body
        }

        if safe:
            print(json.dumps(safe, indent=2, sort_keys=True))
        else:
            print("response_json_keys=%s" % sorted(body.keys()))

    print("raw_token_printed=False")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        required=True,
        choices=("inspect", "jwks", "validate", "call-api"),
    )
    parser.add_argument(
        "--fault",
        default="none",
        choices=("none", "malformed", "unknown-kid", "signature"),
    )
    parser.add_argument("--api-url")
    args = parser.parse_args()

    token = read_token()
    token = apply_fault(token, args.fault)

    if args.action == "inspect":
        action_inspect(token)
    elif args.action == "jwks":
        action_jwks(token)
    elif args.action == "validate":
        action_validate(token)
    elif args.action == "call-api":
        action_call_api(token, args.api_url)


if __name__ == "__main__":
    main()
