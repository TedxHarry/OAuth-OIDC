#!/usr/bin/env python3
"""Day 11 Client Credentials service client.

This helper authenticates an API Services client to a Custom Authorization
Server, keeps the access token in memory, and reuses it for multiple API calls.

Dependencies:
    python -m pip install requests

Required environment variables:
    OKTA_SERVICE_ISSUER
    OKTA_SERVICE_CLIENT_ID
    OKTA_SERVICE_CLIENT_SECRET

Optional environment variables:
    DAY11_SERVICE_SCOPE
        Defaults to employee.report.read.

Example:
    python scripts/python/day11_service_client.py \
      --api-url http://localhost:7100/api/service-report \
      --repeat 3

Security:
- The client secret is read from an environment variable.
- The access token is never printed.
- The token cache exists only in process memory.
"""

import argparse
import base64
import json
import os
import time

import requests


ISSUER = os.environ.get("OKTA_SERVICE_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("OKTA_SERVICE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OKTA_SERVICE_CLIENT_SECRET", "")
SCOPE = os.environ.get("DAY11_SERVICE_SCOPE", "employee.report.read")

if not ISSUER or not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Set OKTA_SERVICE_ISSUER, OKTA_SERVICE_CLIENT_ID, and "
        "OKTA_SERVICE_CLIENT_SECRET before running the Day 11 client."
    )


def fetch_json(url):
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


METADATA = fetch_json(ISSUER + "/.well-known/openid-configuration")

if METADATA.get("issuer") != ISSUER:
    raise SystemExit(
        "Discovery issuer mismatch. Expected %r, got %r."
        % (ISSUER, METADATA.get("issuer"))
    )

TOKEN_ENDPOINT = METADATA.get("token_endpoint")

if not TOKEN_ENDPOINT:
    raise SystemExit("Discovery metadata did not contain token_endpoint.")


def decode_unverified_payload(token):
    parts = token.split(".")

    if len(parts) != 3:
        return {}

    try:
        padding = "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(parts[1] + padding)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


class ServiceTokenCache:
    def __init__(self):
        self.access_token = None
        self.expires_at = 0
        self.acquisition_count = 0

    def usable(self):
        return (
            self.access_token is not None
            and time.time() < self.expires_at - 30
        )

    def acquire(self):
        response = requests.post(
            TOKEN_ENDPOINT,
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={
                "grant_type": "client_credentials",
                "scope": SCOPE,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=15,
        )

        if response.status_code != 200:
            try:
                body = response.json()
            except ValueError:
                body = {"error": response.text}

            raise RuntimeError(
                "Token acquisition failed with HTTP %s: %s"
                % (response.status_code, body)
            )

        body = response.json()
        token = body.get("access_token")
        expires_in = int(body.get("expires_in", 0))

        if not token or expires_in <= 0:
            raise RuntimeError(
                "Token response did not contain a usable access_token/expires_in."
            )

        self.access_token = token
        self.expires_at = time.time() + expires_in
        self.acquisition_count += 1

        payload = decode_unverified_payload(token)

        print("")
        print("TOKEN ACQUIRED")
        print("==============")
        print("token_type=%s" % body.get("token_type"))
        print("expires_in=%s" % expires_in)
        print("response_scope=%s" % body.get("scope"))
        print("jwt_iss=%s" % payload.get("iss"))
        print("jwt_aud=%s" % payload.get("aud"))
        print("jwt_cid=%s" % payload.get("cid"))
        print("jwt_scp=%s" % payload.get("scp"))
        print("jwt_uid_present=%s" % ("uid" in payload))
        print("jwt_sub_present=%s" % ("sub" in payload))
        print("id_token_present=%s" % ("id_token" in body))
        print("refresh_token_present=%s" % ("refresh_token" in body))
        print("")
        print("Inspection note:")
        print("These JWT fields were decoded for observation only.")
        print("The Employee API performs the actual validation.")

    def get(self):
        if not self.usable():
            self.acquire()

        return self.access_token


def call_api(url, token, call_number):
    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
        },
        timeout=15,
    )

    print("")
    print("API CALL %s" % call_number)
    print("==========")
    print("http_status=%s" % response.status_code)
    print(
        "x_correlation_id=%s"
        % response.headers.get("X-Correlation-ID")
    )

    try:
        body = response.json()
    except ValueError:
        body = {"body": response.text}

    print(json.dumps(body, indent=2, sort_keys=True))

    return response.status_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-url",
        default="http://localhost:7100/api/service-report",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=2,
    )
    args = parser.parse_args()

    if args.repeat < 1:
        raise SystemExit("--repeat must be at least 1.")

    cache = ServiceTokenCache()

    for index in range(1, args.repeat + 1):
        token = cache.get()
        call_api(args.api_url, token, index)

    print("")
    print("TOKEN CACHE SUMMARY")
    print("===================")
    print("api_calls=%s" % args.repeat)
    print("token_acquisitions=%s" % cache.acquisition_count)
    print("raw_access_token_printed=False")
    print("raw_client_secret_printed=False")


if __name__ == "__main__":
    main()
