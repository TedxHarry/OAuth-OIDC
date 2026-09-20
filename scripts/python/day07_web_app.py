#!/usr/bin/env python3
"""Day 7 server-side Web Application lab.

This sample is intentionally small and readable. It demonstrates where OAuth
responsibility lives in a confidential server-side Web Application.

Dependencies:
    python -m pip install Flask requests "PyJWT[crypto]"

Required environment variables:
    OKTA_ISSUER
    OKTA_CLIENT_ID
    OKTA_CLIENT_SECRET

Expected redirect URI:
    http://localhost:5000/callback

Important:
- OAuth transaction state and tokens are kept in server memory.
- The browser receives only opaque cookies for the pending transaction and
  local application session.
- The in-memory stores and localhost cookie settings are for training only.
  They are not a production session architecture.
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
PORT = 5000
REDIRECT_URI = "http://localhost:5000/callback"
TX_COOKIE = "day07_tx"
SESSION_COOKIE = "day07_session"

ISSUER = os.environ.get("OKTA_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("OKTA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OKTA_CLIENT_SECRET", "")

if not ISSUER or not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Set OKTA_ISSUER, OKTA_CLIENT_ID, and OKTA_CLIENT_SECRET "
        "before starting the Day 7 Web Application."
    )


def get_json(url):
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"
METADATA = get_json(DISCOVERY_URL)

if METADATA.get("issuer") != ISSUER:
    raise SystemExit(
        "Discovery issuer mismatch. "
        "Expected %r, got %r."
        % (ISSUER, METADATA.get("issuer"))
    )

AUTHORIZATION_ENDPOINT = METADATA["authorization_endpoint"]
TOKEN_ENDPOINT = METADATA["token_endpoint"]
JWKS_URI = METADATA["jwks_uri"]

app = Flask(__name__)

# Training-only in-memory stores.
PENDING_TRANSACTIONS = {}
APPLICATION_SESSIONS = {}


def base64url_no_padding(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce_pair():
    verifier = secrets.token_urlsafe(64)

    if not 43 <= len(verifier) <= 128:
        raise RuntimeError("Generated PKCE verifier length is outside 43-128.")

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64url_no_padding(digest)
    return verifier, challenge


def current_session():
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        return None

    return APPLICATION_SESSIONS.get(session_id)


def safe_claims(claims):
    allowed = (
        "sub",
        "name",
        "preferred_username",
        "email",
        "iss",
        "aud",
        "iat",
        "exp",
    )
    return {key: claims.get(key) for key in allowed if key in claims}


def page(title, body):
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>%s</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }
    pre { background: #f4f4f4; padding: 12px; overflow: auto; }
    a, button { font-size: 1rem; }
  </style>
</head>
<body>
  <h1>%s</h1>
  %s
</body>
</html>""" % (html.escape(title), html.escape(title), body)


@app.get("/")
def home():
    session_data = current_session()

    if not session_data:
        body = """
<p>Status: <strong>Not signed in to this local application</strong></p>
<p><a href="/login">Sign in with Okta</a></p>
<p>After sign-in, inspect the browser Network tab and Application/Cookies.</p>
"""
        return page("Day 7 Server-Side Web Application", body)

    claims = session_data["claims"]

    body = """
<p>Status: <strong>Signed in to this local application</strong></p>
<p>The browser has an opaque HttpOnly application-session cookie.</p>
<p>The OAuth tokens remain in server memory and aren't rendered into this page.</p>
<h2>Validated ID-token claim summary</h2>
<pre>%s</pre>
<form method="post" action="/logout-local">
  <button type="submit">Destroy local application session</button>
</form>
<p><a href="/debug/session">View safe server-side session summary</a></p>
""" % html.escape(str(claims))

    return page("Day 7 Server-Side Web Application", body)


@app.get("/login")
def login():
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier, challenge = create_pkce_pair()
    transaction_id = secrets.token_urlsafe(32)

    PENDING_TRANSACTIONS[transaction_id] = {
        "state": state,
        "nonce": nonce,
        "code_verifier": verifier,
        "created_at": time.time(),
    }

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    authorize_url = AUTHORIZATION_ENDPOINT + "?" + urlencode(params)

    print("[Day 7 Web] Created server-side OAuth transaction.")
    print("[Day 7 Web] Redirecting browser to /authorize.")

    response = make_response(redirect(authorize_url))
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
    print("[Day 7 Web] Browser reached /callback.")

    error = request.args.get("error")
    if error:
        description = request.args.get("error_description", "")
        return page(
            "OAuth authorization error",
            "<p>%s</p><pre>%s</pre>"
            % (html.escape(error), html.escape(description)),
        ), 400

    code = request.args.get("code")
    returned_state = request.args.get("state")
    transaction_id = request.cookies.get(TX_COOKIE)

    if not code or not returned_state:
        return page(
            "Callback error",
            "<p>Missing authorization code or state.</p>",
        ), 400

    if not transaction_id:
        return page(
            "Callback error",
            "<p>Pending transaction cookie is missing.</p>",
        ), 400

    transaction = PENDING_TRANSACTIONS.pop(transaction_id, None)

    if not transaction:
        return page(
            "Callback error",
            "<p>Pending server-side OAuth transaction wasn't found.</p>",
        ), 400

    if time.time() - transaction["created_at"] > 300:
        return page(
            "Callback error",
            "<p>Pending OAuth transaction expired.</p>",
        ), 400

    if not secrets.compare_digest(returned_state, transaction["state"]):
        return page(
            "Callback error",
            "<p>State validation failed. Token exchange wasn't attempted.</p>",
        ), 400

    print("[Day 7 Web] State validation passed.")
    print("[Day 7 Web] Backend is now calling /token.")

    token_response = requests.post(
        TOKEN_ENDPOINT,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": transaction["code_verifier"],
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=15,
    )

    if token_response.status_code != 200:
        try:
            error_body = token_response.json()
        except ValueError:
            error_body = {"error": token_response.text}

        print(
            "[Day 7 Web] Token request failed with HTTP %s."
            % token_response.status_code
        )

        return page(
            "Token exchange failed",
            "<p>Backend /token request failed.</p>"
            "<pre>%s</pre>"
            % html.escape(str(error_body)),
        ), 502

    tokens = token_response.json()
    id_token = tokens.get("id_token")

    if not id_token:
        return page(
            "Token validation failed",
            "<p>No ID token was returned.</p>",
        ), 502

    try:
        header = jwt.get_unverified_header(id_token)

        if header.get("alg") != "RS256":
            raise ValueError(
                "Expected RS256 ID token, got %r." % header.get("alg")
            )

        signing_key = PyJWKClient(JWKS_URI).get_signing_key_from_jwt(id_token)

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

        if claims.get("nonce") != transaction["nonce"]:
            raise ValueError("Nonce validation failed.")

    except Exception as exc:
        print("[Day 7 Web] ID token validation failed: %s" % exc)

        return page(
            "Token validation failed",
            "<p>ID token validation failed.</p><pre>%s</pre>"
            % html.escape(str(exc)),
        ), 502

    print("[Day 7 Web] Backend token exchange succeeded.")
    print("[Day 7 Web] ID token validation succeeded.")
    print("[Day 7 Web] Creating local application session.")

    session_id = secrets.token_urlsafe(32)

    APPLICATION_SESSIONS[session_id] = {
        "claims": safe_claims(claims),
        "oauth_tokens": tokens,
        "created_at": time.time(),
    }

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


@app.post("/logout-local")
def logout_local():
    session_id = request.cookies.get(SESSION_COOKIE)

    if session_id:
        APPLICATION_SESSIONS.pop(session_id, None)

    response = make_response(redirect("/"))
    response.delete_cookie(SESSION_COOKIE, path="/")

    print("[Day 7 Web] Local application session destroyed.")
    print("[Day 7 Web] This route does not end the Okta browser session.")

    return response


@app.get("/debug/session")
def debug_session():
    session_data = current_session()

    if not session_data:
        return page(
            "Day 7 Safe Session Summary",
            "<p>No local application session exists.</p>",
        ), 401

    summary = {
        "validated_claims": session_data["claims"],
        "id_token_present_server_side": bool(
            session_data["oauth_tokens"].get("id_token")
        ),
        "access_token_present_server_side": bool(
            session_data["oauth_tokens"].get("access_token")
        ),
        "refresh_token_present_server_side": bool(
            session_data["oauth_tokens"].get("refresh_token")
        ),
        "raw_tokens_rendered_to_browser": False,
    }

    return page(
        "Day 7 Safe Session Summary",
        "<pre>%s</pre>" % html.escape(str(summary)),
    )


if __name__ == "__main__":
    print("Day 7 server-side Web Application")
    print("Issuer: %s" % ISSUER)
    print("Redirect URI: %s" % REDIRECT_URI)
    print("Open: http://localhost:5000")
    print("")
    print("Training note:")
    print("- OAuth tokens and pending transactions are stored in server memory.")
    print("- Browser gets opaque HttpOnly cookies.")
    print("- Local HTTP cookie settings are not production settings.")
    app.run(host=HOST, port=PORT, debug=False)
