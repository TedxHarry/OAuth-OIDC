#!/usr/bin/env python3
"""Day 13 browser/authentication troubleshooting fault harness.

This is a diagnostic training app, not production code.

Dependencies:
    python -m pip install Flask requests "PyJWT[crypto]"

Required environment variables:
    OKTA_ISSUER
    OKTA_CLIENT_ID
    OKTA_CLIENT_SECRET

Register this normal redirect URI on the Web Application:
    http://localhost:5300/callback

Faults are selected through /login?fault=<name>:
    none
    redirect
    state
    lost
    nonce
    session

Security:
- Raw tokens, authorization codes, PKCE verifiers, client secrets, and cookie
  values are never printed.
- Faults are local training controls only.
"""

import base64
import hashlib
import html
import os
import secrets
import time
from urllib.parse import urlencode

import jwt
import requests
from flask import Flask, make_response, redirect, request
from jwt import PyJWKClient


HOST = "localhost"
PORT = 5300
REDIRECT_URI = "http://localhost:5300/callback"
WRONG_REDIRECT_URI = "http://localhost:5300/wrong-callback"

TX_COOKIE = "day13_tx"
SESSION_COOKIE = "day13_session"

ISSUER = os.environ.get("OKTA_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("OKTA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OKTA_CLIENT_SECRET", "")

if not ISSUER or not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Set OKTA_ISSUER, OKTA_CLIENT_ID, and OKTA_CLIENT_SECRET."
    )


def get_json(url):
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


METADATA = get_json(ISSUER + "/.well-known/openid-configuration")

if METADATA.get("issuer") != ISSUER:
    raise SystemExit(
        "Discovery issuer mismatch. Expected %r, got %r."
        % (ISSUER, METADATA.get("issuer"))
    )

AUTHORIZATION_ENDPOINT = METADATA["authorization_endpoint"]
TOKEN_ENDPOINT = METADATA["token_endpoint"]
JWKS_URI = METADATA["jwks_uri"]
JWK_CLIENT = PyJWKClient(JWKS_URI)

app = Flask(__name__)

PENDING = {}
SESSIONS = {}


def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, b64url(digest)


def page(title, body):
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>%s</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 950px; margin: 40px auto; padding: 0 20px; }
    a { display: inline-block; margin: 6px 10px 6px 0; }
    pre { background: #f4f4f4; padding: 12px; overflow: auto; }
  </style>
</head>
<body>
  <h1>%s</h1>
  %s
</body>
</html>""" % (html.escape(title), html.escape(title), body)


def current_session():
    sid = request.cookies.get(SESSION_COOKIE)
    if not sid:
        return None
    return SESSIONS.get(sid)


@app.get("/")
def home():
    session_data = current_session()

    status = (
        "Local application session active"
        if session_data
        else "No local application session"
    )

    body = """
<p>Status: <strong>%s</strong></p>

<h2>Controlled sign-in cases</h2>
<p><a href="/login?fault=none">Normal sign-in</a></p>
<p><a href="/login?fault=redirect">Fault: unregistered redirect URI</a></p>
<p><a href="/login?fault=state">Fault: state mismatch</a></p>
<p><a href="/login?fault=lost">Fault: pending transaction missing</a></p>
<p><a href="/login?fault=nonce">Fault: nonce mismatch</a></p>
<p><a href="/login?fault=session">Fault: OAuth succeeds, local session not created</a></p>

<h2>Evidence rule</h2>
<pre>Last confirmed successful step:
First failed step:
Browser evidence:
Backend evidence:
Okta System Log evidence:
Root cause:
Proof after fix:</pre>
""" % html.escape(status)

    return page("Day 13 Web Troubleshooting Harness", body)


@app.get("/login")
def login():
    fault = request.args.get("fault", "none")

    if fault not in {"none", "redirect", "state", "lost", "nonce", "session"}:
        return page("Invalid fault", "<p>Unknown fault mode.</p>"), 400

    sent_state = secrets.token_urlsafe(32)
    sent_nonce = secrets.token_urlsafe(32)
    verifier, challenge = create_pkce()
    transaction_id = secrets.token_urlsafe(32)

    expected_state = sent_state
    expected_nonce = sent_nonce

    if fault == "state":
        expected_state = sent_state + "-intentionally-different"

    if fault == "nonce":
        expected_nonce = sent_nonce + "-intentionally-different"

    transaction = {
        "expected_state": expected_state,
        "expected_nonce": expected_nonce,
        "verifier": verifier,
        "fault": fault,
        "created_at": time.time(),
    }

    if fault != "lost":
        PENDING[transaction_id] = transaction

    redirect_uri = WRONG_REDIRECT_URI if fault == "redirect" else REDIRECT_URI

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": redirect_uri,
        "state": sent_state,
        "nonce": sent_nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    print("[Day 13] transaction_created=True")
    print("[Day 13] fault=%s" % fault)
    print("[Day 13] redirect_uri=%s" % redirect_uri)
    print("[Day 13] raw_credentials_logged=False")

    response = make_response(
        redirect(AUTHORIZATION_ENDPOINT + "?" + urlencode(params))
    )
    response.set_cookie(
        TX_COOKIE,
        transaction_id,
        max_age=300,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )
    return response


@app.get("/callback")
def callback():
    print("[Day 13] callback_reached=True")

    oauth_error = request.args.get("error")
    if oauth_error:
        return page(
            "Authorization Error",
            "<p>Okta returned an authorization error.</p><pre>%s</pre>"
            % html.escape(
                str(
                    {
                        "error": oauth_error,
                        "error_description": request.args.get(
                            "error_description",
                            "",
                        ),
                    }
                )
            ),
        ), 400

    code = request.args.get("code")
    returned_state = request.args.get("state")
    transaction_id = request.cookies.get(TX_COOKIE)

    if not code or not returned_state or not transaction_id:
        print("[Day 13] callback_input_complete=False")
        return page(
            "Callback Failure",
            "<p>Code, state, or transaction cookie is missing.</p>",
        ), 400

    transaction = PENDING.pop(transaction_id, None)

    if not transaction:
        print("[Day 13] pending_transaction_found=False")
        print("[Day 13] token_request_attempted=False")
        return page(
            "Pending Transaction Missing",
            "<p>The callback reached the application, but the expected "
            "server-side transaction record does not exist.</p>",
        ), 400

    print("[Day 13] pending_transaction_found=True")

    if time.time() - transaction["created_at"] > 300:
        print("[Day 13] transaction_expired=True")
        return page(
            "Transaction Expired",
            "<p>The pending transaction expired.</p>",
        ), 400

    if not secrets.compare_digest(
        returned_state,
        transaction["expected_state"],
    ):
        print("[Day 13] state_validation=False")
        print("[Day 13] token_request_attempted=False")
        return page(
            "State Validation Failed",
            "<p>Callback reached the app, but state validation failed.</p>",
        ), 400

    print("[Day 13] state_validation=True")
    print("[Day 13] token_request_attempted=True")

    token_response = requests.post(
        TOKEN_ENDPOINT,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": transaction["verifier"],
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=15,
    )

    if token_response.status_code != 200:
        print("[Day 13] token_exchange=False")
        print("[Day 13] token_http=%s" % token_response.status_code)
        return page(
            "Token Exchange Failed",
            "<p>Backend token request failed with HTTP %s.</p>"
            % token_response.status_code,
        ), 502

    print("[Day 13] token_exchange=True")

    tokens = token_response.json()
    id_token = tokens.get("id_token")

    if not id_token:
        print("[Day 13] id_token_present=False")
        return page(
            "OIDC Validation Failed",
            "<p>No ID token was returned.</p>",
        ), 502

    try:
        header = jwt.get_unverified_header(id_token)

        if header.get("alg") != "RS256":
            raise ValueError("Unexpected ID token signing algorithm.")

        signing_key = JWK_CLIENT.get_signing_key_from_jwt(id_token)

        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=ISSUER,
            leeway=60,
            options={
                "require": ["iss", "sub", "aud", "iat", "exp"],
            },
        )

        if claims.get("nonce") != transaction["expected_nonce"]:
            raise ValueError("Nonce validation failed.")

    except Exception as exc:
        print("[Day 13] oidc_validation=False")
        print("[Day 13] oidc_failure=%s" % type(exc).__name__)
        return page(
            "OIDC Validation Failed",
            "<p>Token exchange succeeded, but OIDC validation failed.</p>"
            "<pre>%s</pre>" % html.escape(str(exc)),
        ), 502

    print("[Day 13] oidc_validation=True")

    if transaction["fault"] == "session":
        print("[Day 13] local_session_created=False")
        response = make_response(
            page(
                "OAuth Succeeded, Local Session Failed",
                "<p>Authorization, token exchange, and OIDC validation "
                "succeeded.</p>"
                "<p>The training fault intentionally skipped creation of "
                "the local application session.</p>"
                "<p><a href='/'>Return home</a></p>",
            )
        )
        response.delete_cookie(TX_COOKIE, path="/")
        return response

    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "created_at": time.time(),
        "sub": claims.get("sub"),
    }

    print("[Day 13] local_session_created=True")

    response = make_response(redirect("/"))
    response.delete_cookie(TX_COOKIE, path="/")
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        max_age=3600,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )
    return response


if __name__ == "__main__":
    print("Day 13 browser/authentication troubleshooting harness")
    print("Issuer: %s" % ISSUER)
    print("Normal redirect URI: %s" % REDIRECT_URI)
    print("Open: http://localhost:%s" % PORT)
    print("")
    print("Register only the normal redirect URI.")
    print("Do not register the intentionally wrong redirect URI.")
    print("Raw OAuth credentials are not logged.")
    app.run(host=HOST, port=PORT, debug=False)
