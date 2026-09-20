#!/usr/bin/env python3
"""Inspect a Day 9 Custom Authorization Server access token.

This script decodes only. It does not validate the token.

Run:
    python scripts/python/day09_inspect_access_token.py

Paste the access token when prompted. Input is hidden.
"""

import base64
import getpass
import json
from datetime import datetime, timezone


def decode_json_segment(segment):
    padding = "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(segment + padding)
    return json.loads(raw.decode("utf-8"))


def format_epoch(value):
    if not isinstance(value, (int, float)):
        return None

    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def main():
    token = getpass.getpass(
        "Paste access token for Day 9 inspection (input hidden): "
    ).strip()

    parts = token.split(".")

    if len(parts) != 3:
        raise SystemExit("Expected a three-part JWT access token.")

    try:
        header = decode_json_segment(parts[0])
        payload = decode_json_segment(parts[1])
    except Exception as exc:
        raise SystemExit("Unable to decode JWT: %s" % exc) from exc

    print("")
    print("IMPORTANT")
    print("=========")
    print("This token was decoded only.")
    print("The Day 9 API performs validation.")

    print("")
    print("HEADER")
    print("======")
    print(json.dumps(header, indent=2, sort_keys=True))

    print("")
    print("SELECTED CLAIMS")
    print("===============")

    for claim in (
        "iss",
        "aud",
        "sub",
        "cid",
        "scp",
        "department",
        "groups",
        "iat",
        "exp",
    ):
        value = payload.get(claim)
        print("%s=%s" % (claim, value))

        if claim in ("iat", "exp") and value is not None:
            formatted = format_epoch(value)
            if formatted:
                print("%s_utc=%s" % (claim, formatted))

    iat = payload.get("iat")
    exp = payload.get("exp")

    if isinstance(iat, (int, float)) and isinstance(exp, (int, float)):
        print("")
        print("TOKEN LIFETIME")
        print("==============")
        print("lifetime_seconds=%s" % int(exp - iat))
        print("lifetime_minutes=%s" % ((exp - iat) / 60))

    print("")
    print("REMINDER")
    print("========")
    print("department and groups are contextual claims in this lab.")
    print("salary.read in scp is the permission enforced by /api/salary.")


if __name__ == "__main__":
    main()
