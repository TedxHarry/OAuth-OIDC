#!/usr/bin/env python3
"""Generate a local RSA key pair for the Day 12 private_key_jwt lab.

Dependencies:
    python -m pip install cryptography

Default output:
    secrets/day12/day12_private_key.pem
    secrets/day12/day12_public_jwk.json

The repository ignores secrets/ and *.pem.

Only the PUBLIC JWK is registered with Okta.
The PRIVATE key stays with the automation.
"""

import argparse
import base64
import json
import os
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def b64url_uint(value):
    length = max(1, (value.bit_length() + 7) // 8)
    raw = value.to_bytes(length, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="secrets/day12",
        help="Local output directory. Keep it outside source control.",
    )
    parser.add_argument(
        "--kid",
        default=None,
        help="Optional key ID. A random ID is generated when omitted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    private_path = output_dir / "day12_private_key.pem"
    public_jwk_path = output_dir / "day12_public_jwk.json"

    if not args.force and (private_path.exists() or public_jwk_path.exists()):
        raise SystemExit(
            "Output already exists. Use another --output-dir or --force."
        )

    kid = args.kid or ("day12-" + secrets.token_hex(8))

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_numbers = private_key.public_key().public_numbers()

    public_jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": b64url_uint(public_numbers.n),
        "e": b64url_uint(public_numbers.e),
    }

    private_path.write_bytes(private_pem)
    public_jwk_path.write_text(
        json.dumps(public_jwk, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass

    print("")
    print("DAY 12 KEY PAIR CREATED")
    print("=======================")
    print("kid=%s" % kid)
    print("private_key_path=%s" % private_path)
    print("public_jwk_path=%s" % public_jwk_path)
    print("")
    print("NEXT STEP")
    print("=========")
    print("Register only the PUBLIC JWK with the Okta API Services app.")
    print("Keep the private PEM local and protected.")
    print("")
    print("GIT SAFETY")
    print("==========")
    print("The repository .gitignore excludes secrets/ and *.pem.")


if __name__ == "__main__":
    main()
