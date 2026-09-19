#!/usr/bin/env python3
"""Generate an RFC 7636-style PKCE verifier and S256 challenge."""

import base64
import hashlib
import secrets


def base64url_no_padding(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def main() -> None:
    # token_urlsafe produces a high-entropy URL-safe verifier.
    verifier = secrets.token_urlsafe(64)

    challenge = base64url_no_padding(
        hashlib.sha256(verifier.encode("ascii")).digest()
    )

    print(f"code_verifier={verifier}")
    print(f"code_challenge={challenge}")
    print("code_challenge_method=S256")


if __name__ == "__main__":
    main()
