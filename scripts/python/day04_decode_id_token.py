#!/usr/bin/env python3
"""Decode an ID token for Day 4 inspection.

This script DOES NOT validate the signature or claims.

Run:
    python scripts/python/day04_decode_id_token.py

Paste the ID token when prompted. Input is hidden so the token isn't echoed
to the terminal while you paste it.
"""

import base64
import getpass
import json
from datetime import datetime, timezone


def decode_base64url_json(segment):
    padding = "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(segment + padding)
    return json.loads(raw.decode("utf-8"))


def format_epoch(value):
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def main():
    token = getpass.getpass("Paste ID token (input hidden): ").strip()

    parts = token.split(".")
    if len(parts) != 3:
        raise SystemExit("Expected a JWT with three dot-separated sections.")

    try:
        header = decode_base64url_json(parts[0])
        payload = decode_base64url_json(parts[1])
    except Exception as exc:
        raise SystemExit(f"Unable to decode JWT: {exc}") from exc

    print("\nIMPORTANT")
    print("=========")
    print("This token was decoded only.")
    print("The signature and claims were NOT validated.")

    print("\nHEADER")
    print("======")
    print(json.dumps(header, indent=2, sort_keys=True))

    print("\nPAYLOAD")
    print("=======")
    print(json.dumps(payload, indent=2, sort_keys=True))

    print("\nSELECTED CLAIMS")
    print("===============")

    for claim in ("iss", "sub", "aud", "iat", "exp", "nonce", "email"):
        value = payload.get(claim)
        print(f"{claim}={value}")

        if claim in ("iat", "exp") and value is not None:
            formatted = format_epoch(value)
            if formatted:
                print(f"{claim}_utc={formatted}")

    print("\nREMINDER")
    print("========")
    print("Readable claims are not proof that the token is trustworthy.")
    print("Day 5 performs actual JWT validation.")


if __name__ == "__main__":
    main()
