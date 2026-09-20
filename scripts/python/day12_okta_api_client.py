#!/usr/bin/env python3
"""Day 12 Okta Management API OAuth service client.

This helper:
- builds a fresh private_key_jwt client assertion
- requests an access token from the Org Authorization Server
- treats the Org-AS access token as opaque
- calls selected Okta Management API endpoints

Dependencies:
    python -m pip install requests "PyJWT[crypto]" cryptography

Required environment variables:
    OKTA_DOMAIN
        Example: https://integrator-123456.okta.com
    OKTA_API_CLIENT_ID
    OKTA_API_PRIVATE_KEY
        Path to private PEM generated locally.
    OKTA_API_KEY_ID

Optional:
    OKTA_API_SCOPES
        Defaults to: okta.users.read okta.groups.read

Examples:
    python scripts/python/day12_okta_api_client.py --action list-users
    python scripts/python/day12_okta_api_client.py --action list-groups
    python scripts/python/day12_okta_api_client.py --action get-user --user-id 00u...
    python scripts/python/day12_okta_api_client.py --action token-only --fault wrong-aud

Controlled write:
    python scripts/python/day12_okta_api_client.py \
      --action add-user-to-group \
      --user-id 00u... \
      --group-id 00g... \
      --allow-write

Security:
- The private key is read from a local file.
- The full client assertion is never printed.
- The access token is never printed or decoded.
"""

import argparse
import json
import os
import time
import uuid
from pathlib import Path

import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN", "").strip().rstrip("/")
CLIENT_ID = os.environ.get("OKTA_API_CLIENT_ID", "").strip()
PRIVATE_KEY_PATH = os.environ.get("OKTA_API_PRIVATE_KEY", "").strip()
KEY_ID = os.environ.get("OKTA_API_KEY_ID", "").strip()
DEFAULT_SCOPES = os.environ.get(
    "OKTA_API_SCOPES",
    "okta.users.read okta.groups.read",
).strip()

if not OKTA_DOMAIN or not CLIENT_ID or not PRIVATE_KEY_PATH or not KEY_ID:
    raise SystemExit(
        "Set OKTA_DOMAIN, OKTA_API_CLIENT_ID, OKTA_API_PRIVATE_KEY, "
        "and OKTA_API_KEY_ID."
    )

if not OKTA_DOMAIN.startswith("https://"):
    raise SystemExit("OKTA_DOMAIN must start with https://")

TOKEN_ENDPOINT = OKTA_DOMAIN + "/oauth2/v1/token"


def load_private_key():
    path = Path(PRIVATE_KEY_PATH)

    if not path.is_file():
        raise SystemExit("Private key file not found: %s" % path)

    return path.read_bytes()


def create_ephemeral_wrong_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def build_assertion(fault="none"):
    now = int(time.time())
    audience = TOKEN_ENDPOINT
    kid = KEY_ID
    signing_key = load_private_key()

    if fault == "wrong-aud":
        audience = OKTA_DOMAIN + "/oauth2/default/v1/token"
    elif fault == "wrong-kid":
        kid = KEY_ID + "-not-registered"
    elif fault == "wrong-key":
        signing_key = create_ephemeral_wrong_key()

    if fault == "expired":
        issued_at = now - 300
        expires_at = now - 60
    else:
        issued_at = now
        expires_at = now + 300

    claims = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": audience,
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }

    headers = {
        "alg": "RS256",
        "kid": kid,
        "typ": "JWT",
    }

    assertion = jwt.encode(
        claims,
        signing_key,
        algorithm="RS256",
        headers=headers,
    )

    safe_metadata = {
        "alg": "RS256",
        "kid": kid,
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": audience,
        "iat": issued_at,
        "exp": expires_at,
        "jti": claims["jti"],
    }

    return assertion, safe_metadata


def request_access_token(assertion, scopes):
    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "client_credentials",
            "scope": scopes,
            "client_assertion_type": ASSERTION_TYPE,
            "client_assertion": assertion,
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=20,
    )

    try:
        body = response.json()
    except ValueError:
        body = {"body": response.text}

    return response, body


def print_assertion_metadata(metadata):
    print("")
    print("CLIENT ASSERTION METADATA")
    print("=========================")
    for key in ("alg", "kid", "iss", "sub", "aud", "iat", "exp", "jti"):
        print("%s=%s" % (key, metadata.get(key)))
    print("full_assertion_printed=False")


def print_token_result(response, body):
    print("")
    print("TOKEN RESPONSE")
    print("==============")
    print("http_status=%s" % response.status_code)

    if response.status_code == 200:
        print("token_type=%s" % body.get("token_type"))
        print("expires_in=%s" % body.get("expires_in"))
        print("scope=%s" % body.get("scope"))
        print("access_token_present=%s" % bool(body.get("access_token")))
        print("access_token_decoded=False")
        print("access_token_printed=False")
    else:
        safe_error = {
            "error": body.get("error"),
            "error_description": body.get("error_description"),
        }
        print(json.dumps(safe_error, indent=2, sort_keys=True))


def okta_api_request(method, path, token):
    response = requests.request(
        method,
        OKTA_DOMAIN + path,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        timeout=20,
    )

    try:
        body = response.json() if response.content else None
    except ValueError:
        body = response.text

    print("")
    print("OKTA MANAGEMENT API")
    print("===================")
    print("method=%s" % method)
    print("path=%s" % path)
    print("http_status=%s" % response.status_code)

    for name in (
        "x-okta-request-id",
        "x-request-id",
        "x-rate-limit-limit",
        "x-rate-limit-remaining",
        "x-rate-limit-reset",
    ):
        if response.headers.get(name):
            print("%s=%s" % (name, response.headers.get(name)))

    return response, body


def print_read_summary(action, body):
    if action == "list-users" and isinstance(body, list):
        print("records_returned=%s" % len(body))
        for item in body[:5]:
            print(
                "user id=%s status=%s"
                % (item.get("id"), item.get("status"))
            )

    elif action == "list-groups" and isinstance(body, list):
        print("records_returned=%s" % len(body))
        for item in body[:5]:
            profile = item.get("profile") or {}
            print(
                "group id=%s name=%s"
                % (item.get("id"), profile.get("name"))
            )

    elif action == "get-user" and isinstance(body, dict):
        profile = body.get("profile") or {}
        print("user_id=%s" % body.get("id"))
        print("status=%s" % body.get("status"))
        print("login=%s" % profile.get("login"))

    elif isinstance(body, dict) and body.get("errorCode"):
        safe_error = {
            "errorCode": body.get("errorCode"),
            "errorSummary": body.get("errorSummary"),
            "errorId": body.get("errorId"),
        }
        print(json.dumps(safe_error, indent=2, sort_keys=True))


def require_write_confirmation(args):
    if not args.allow_write:
        raise SystemExit(
            "Write action blocked. Re-run with --allow-write only for the "
            "dedicated Day 12 test group."
        )

    if not args.user_id or not args.group_id:
        raise SystemExit("Write action requires --user-id and --group-id.")


def execute_action(args, token):
    if args.action == "list-users":
        response, body = okta_api_request(
            "GET",
            "/api/v1/users?limit=5",
            token,
        )
        print_read_summary(args.action, body)
        return response.status_code

    if args.action == "get-user":
        if not args.user_id:
            raise SystemExit("--user-id is required for get-user.")

        response, body = okta_api_request(
            "GET",
            "/api/v1/users/" + requests.utils.quote(args.user_id, safe=""),
            token,
        )
        print_read_summary(args.action, body)
        return response.status_code

    if args.action == "list-groups":
        response, body = okta_api_request(
            "GET",
            "/api/v1/groups?limit=5",
            token,
        )
        print_read_summary(args.action, body)
        return response.status_code

    if args.action in ("add-user-to-group", "remove-user-from-group"):
        require_write_confirmation(args)

        method = "PUT" if args.action == "add-user-to-group" else "DELETE"
        path = (
            "/api/v1/groups/"
            + requests.utils.quote(args.group_id, safe="")
            + "/users/"
            + requests.utils.quote(args.user_id, safe="")
        )

        response, body = okta_api_request(method, path, token)

        if response.status_code in (200, 204):
            print("write_result=success")
        else:
            print_read_summary(args.action, body)

        return response.status_code

    raise SystemExit("Unsupported action: %s" % args.action)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        required=True,
        choices=(
            "token-only",
            "list-users",
            "get-user",
            "list-groups",
            "add-user-to-group",
            "remove-user-from-group",
        ),
    )
    parser.add_argument(
        "--scopes",
        default=DEFAULT_SCOPES,
        help="Space-separated Okta API scopes.",
    )
    parser.add_argument("--user-id")
    parser.add_argument("--group-id")
    parser.add_argument("--allow-write", action="store_true")
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Reuse one acquired access token for repeated read calls.",
    )
    parser.add_argument(
        "--fault",
        default="none",
        choices=(
            "none",
            "wrong-aud",
            "wrong-kid",
            "wrong-key",
            "expired",
            "replay",
        ),
    )
    args = parser.parse_args()

    assertion, metadata = build_assertion(
        "none" if args.fault == "replay" else args.fault
    )
    print_assertion_metadata(metadata)

    response, body = request_access_token(assertion, args.scopes)
    print_token_result(response, body)

    if args.fault == "replay":
        print("")
        print("REPLAY TEST")
        print("===========")
        print("Sending the exact same signed assertion again.")
        replay_response, replay_body = request_access_token(
            assertion,
            args.scopes,
        )
        print_token_result(replay_response, replay_body)
        return

    if response.status_code != 200:
        return

    if args.repeat < 1:
        raise SystemExit("--repeat must be at least 1.")

    if args.action in ("add-user-to-group", "remove-user-from-group") and args.repeat != 1:
        raise SystemExit("Write actions require --repeat 1.")

    access_token = body.get("access_token")

    if not access_token:
        raise SystemExit("Token response did not contain access_token.")

    if args.action == "token-only":
        return

    for call_number in range(1, args.repeat + 1):
        print("")
        print("API CALL NUMBER")
        print("===============")
        print(call_number)
        execute_action(args, access_token)

    print("")
    print("TOKEN REUSE SUMMARY")
    print("===================")
    print("token_requests=1")
    print("api_calls=%s" % args.repeat)
    print("client_assertions_created=1")


if __name__ == "__main__":
    main()
