#!/usr/bin/env python3
"""Decode a Day 8 access token for local inspection only.

This script DOES NOT validate the token.

Run:
    python scripts/python/day08_inspect_access_token.py

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
        "Paste access token for inspection (input hidden): "
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
    print("This access token was decoded only.")
    print("The signature and claims were NOT validated.")

    print("")
    print("HEADER")
    print("======")
    print(json.dumps(header, indent=2, sort_keys=True))

    print("")
    print("SELECTED ACCESS-TOKEN CLAIMS")
    print("============================")

    for claim in ("iss", "aud", "sub", "cid", "scp", "iat", "exp"):
        value = payload.get(claim)
        print("%s=%s" % (claim, value))

        if claim in ("iat", "exp") and value is not None:
            formatted = format_epoch(value)
            if formatted:
                print("%s_utc=%s" % (claim, formatted))

    print("")
    print("REMINDER")
    print("========")
    print("Readable claims are not authorization evidence by themselves.")
    print("The Day 8 Employee API performs actual validation.")


if __name__ == "__main__":
    main()
