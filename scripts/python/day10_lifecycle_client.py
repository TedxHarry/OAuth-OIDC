#!/usr/bin/env python3
"""Day 10 public-client lifecycle utility.

Actions:
    userinfo
    introspect-access
    introspect-refresh
    revoke-access
    revoke-refresh

Example:
    python scripts/python/day10_lifecycle_client.py \
      --issuer https://your-org.okta.com/oauth2/aus... \
      --client-id 0oa... \
      --action introspect-access

The token is entered using a hidden prompt and is never printed.
This helper is for the public SPA client used in the course, so revocation and
introspection send client_id rather than a client secret.
"""

import argparse
import getpass
import json
import urllib.error
import urllib.parse
import urllib.request


ACTIONS = (
    "userinfo",
    "introspect-access",
    "introspect-refresh",
    "revoke-access",
    "revoke-refresh",
)


def normalize_issuer(value):
    return value.strip().rstrip("/")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def form_post(url, data, bearer_token=None):
    body = urllib.parse.urlencode(data).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    if bearer_token:
        headers["Authorization"] = "Bearer " + bearer_token

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return response.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw


def bearer_get(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return response.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw


def print_json_or_text(raw):
    if not raw:
        print("<empty response body>")
        return

    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return

    print(json.dumps(value, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--action", required=True, choices=ACTIONS)
    args = parser.parse_args()

    issuer = normalize_issuer(args.issuer)
    metadata = get_json(issuer + "/.well-known/openid-configuration")

    if metadata.get("issuer") != issuer:
        raise SystemExit(
            "Discovery issuer mismatch. Expected %r, got %r."
            % (issuer, metadata.get("issuer"))
        )

    token = getpass.getpass(
        "Paste token for %s (input hidden): " % args.action
    ).strip()

    if not token:
        raise SystemExit("Token is required.")

    if args.action == "userinfo":
        endpoint = metadata.get("userinfo_endpoint")

        if not endpoint:
            raise SystemExit("Discovery metadata has no userinfo_endpoint.")

        status, raw = bearer_get(endpoint, token)

    elif args.action.startswith("introspect-"):
        endpoint = metadata.get("introspection_endpoint")

        if not endpoint:
            raise SystemExit("Discovery metadata has no introspection_endpoint.")

        hint = (
            "access_token"
            if args.action == "introspect-access"
            else "refresh_token"
        )

        status, raw = form_post(
            endpoint,
            {
                "token": token,
                "token_type_hint": hint,
                "client_id": args.client_id,
            },
        )

    else:
        endpoint = metadata.get("revocation_endpoint")

        if not endpoint:
            raise SystemExit("Discovery metadata has no revocation_endpoint.")

        hint = (
            "access_token"
            if args.action == "revoke-access"
            else "refresh_token"
        )

        status, raw = form_post(
            endpoint,
            {
                "token": token,
                "token_type_hint": hint,
                "client_id": args.client_id,
            },
        )

    print("")
    print("HTTP STATUS")
    print("===========")
    print(status)

    print("")
    print("RESPONSE")
    print("========")
    print_json_or_text(raw)

    print("")
    print("SECURITY NOTE")
    print("=============")
    print("The submitted token was not printed by this utility.")


if __name__ == "__main__":
    main()
