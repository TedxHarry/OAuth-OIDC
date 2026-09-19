#!/usr/bin/env python3
"""Create an intentionally invalid JWT for the Day 5 lab.

This script does not sign anything. It changes the header or payload while
keeping the original signature, so validation should fail.

Run:
    python scripts/python/day05_tamper_jwt.py --mode payload

or:
    python scripts/python/day05_tamper_jwt.py --mode kid
"""

import argparse
import base64
import getpass
import json


def decode_segment(segment):
    padding = "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(segment + padding)
    return json.loads(raw.decode("utf-8"))


def encode_segment(value):
    raw = json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("payload", "kid"),
        required=True,
    )
    args = parser.parse_args()

    token = getpass.getpass("Paste valid ID token (input hidden): ").strip()
    parts = token.split(".")

    if len(parts) != 3:
        raise SystemExit("Expected a three-part JWT.")

    header = decode_segment(parts[0])
    payload = decode_segment(parts[1])

    if args.mode == "payload":
        payload["day5_tampered"] = True
    else:
        header["kid"] = "day5-unknown-kid"

    tampered = ".".join(
        (
            encode_segment(header),
            encode_segment(payload),
            parts[2],
        )
    )

    print("\nINTENTIONALLY INVALID JWT")
    print("=========================")
    print(tampered)

    print("\nThis token was modified without creating a new signature.")
    print("It must not pass normal validation.")


if __name__ == "__main__":
    main()
