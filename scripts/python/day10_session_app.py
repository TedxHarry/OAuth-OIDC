#!/usr/bin/env python3
"""Day 10 server-side session lifecycle app.

Purpose:
- Demonstrate local application logout separately from Okta browser-session logout.
- Keep OAuth tokens server-side.
- Use discovery for authorize, token, JWKS, and end-session endpoints.

Dependencies:
    python -m pip install Flask requests "PyJWT[crypto]"

Required environment variables:
    OKTA_ISSUER
    OKTA_CLIENT_ID
    OKTA_CLIENT_SECRET

Okta Web Application redirect URIs:
    Sign-in:  http://localhost:5100/callback
    Sign-out: http://localhost:5100/logged-out

Training note:
The in-memory stores and HTTP localhost cookies are deliberately simple.
They are not a production session store or production cookie configuration.
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
PORT = 5100
REDIRECT_URI = "http://localhost:5100/callback"
POST_LOGOUT_REDIRECT_URI = "http://localhost:5100/logged-out"

TX_COOKIE = "day10_tx"
SESSION_COOKIE = "day10_session"
LOGOUT_COOKIE = "day10_logout_state"

ISSUER = os.environ.get("OKTA_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("OKTA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OKTA_CLIENT_SECRET", "")

if not ISSUER or not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit(
        "Set OKTA_ISSUER, OKTA_CLIENT_ID, and OKTA_CLIENT_SECRET "
        "before starting the Day 10 session app."
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
END_SESSION_ENDPOINT = METADATA.get("end_session_endpoint")

if not END_SESSION_ENDPOINT:
    raise SystemExit(
        "Discovery metadata did not include end_session_endpoint."
    )

JWK_CLIENT = PyJWKClient(JWKS_URI)

app = Flask(__name__)

PENDING_TRANSACTIONS = {}
APPLICATION_SESSIONS = {}


def base64url_no_padding(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_pkce_pair():
    verifier = secrets.token_urlsafe(64)

    if not 43 <= len(verifier) <= 128:
        raise RuntimeError("Generated PKCE verifier length is outside 43-128.")

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64url_no_padding(digest)


def current_session():
    session_id = request.cookies.get(SESSION_COOKIE)

    if not session_id:
        return None

    return APPLICATION_SESSIONS.get(session_id)


def safe_claims(claims):
    keys = (
        "sub",
        "name",
        "preferred_username",
        "email",
        "iss",
        "aud",
        "iat",
        "exp",
    )
    return {key: claims.get(key) for key in keys if key in claims}


def page(title, body):
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>%s</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }
    pre { background: #f4f4f4; padding: 12px; overflow: auto; }
    form { display: inline-block; margin-right: 12px; }
    button, a { font-size: 1rem; }
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
        return page(
            "Day 10 Session Lifecycle",
            """
<p>Status: <strong>No local application session</strong></p>
<p><a href="/login">Sign in with Okta</a></p>
<p>
If an Okta browser session is still active, signing in again may not require
another credential prompt.
</p>
""",
        )

    body = """
<p>Status: <strong>Local application session active</strong></p>
<pre>%s</pre>

<form method="post" action="/logout-local">
  <button type="submit">Local Logout Only</button>
</form>

<form method="post" action="/logout-okta">
  <button type="submit">Local Logout + Okta Browser Logout</button>
</form>

<p>
Neither button intentionally revokes the OAuth access/refresh tokens.
Token revocation is tested separately in the Day 10 lifecycle lab.
</p>
""" % html.escape(str(session_data["claims"]))

    return page("Day 10 Session Lifecycle", body)


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

    print("[Day 10 Session] Started authorization transaction.")
    return response


@app.get("/callback")
def callback():
    error = request.args.get("error")

    if error:
        return page(
            "Authorization error",
            "<p>%s</p><pre>%s</pre>"
            % (
                html.escape(error),
                html.escape(request.args.get("error_description", "")),
            ),
        ), 400

    code = request.args.get("code")
    returned_state = request.args.get("state")
    transaction_id = request.cookies.get(TX_COOKIE)

    if not code or not returned_state or not transaction_id:
        return page(
            "Callback error",
            "<p>Missing code, state, or pending transaction cookie.</p>",
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
            "<p>Pending authorization transaction expired.</p>",
        ), 400

    if not secrets.compare_digest(returned_state, transaction["state"]):
        return page(
            "Callback error",
            "<p>State validation failed.</p>",
        ), 400

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
        return page(
            "Token exchange failed",
            "<p>Backend token request failed with HTTP %s.</p>"
            % token_response.status_code,
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
            raise ValueError("Unexpected ID-token algorithm.")

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

        if claims.get("nonce") != transaction["nonce"]:
            raise ValueError("Nonce validation failed.")

    except Exception as exc:
        print("[Day 10 Session] ID-token validation failed: %s" % exc)
        return page(
            "Token validation failed",
            "<p>ID-token validation failed.</p>",
        ), 502

    session_id = secrets.token_urlsafe(32)

    APPLICATION_SESSIONS[session_id] = {
        "claims": safe_claims(claims),
        "id_token": id_token,
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

    print("[Day 10 Session] Local application session created.")
    return response


@app.post("/logout-local")
def logout_local():
    session_id = request.cookies.get(SESSION_COOKIE)

    if session_id:
        APPLICATION_SESSIONS.pop(session_id, None)

    response = make_response(redirect("/"))
    response.delete_cookie(SESSION_COOKIE, path="/")

    print("[Day 10 Session] Local application session destroyed.")
    print("[Day 10 Session] Okta browser session was not ended.")
    return response


@app.post("/logout-okta")
def logout_okta():
    session_id = request.cookies.get(SESSION_COOKIE)
    session_data = APPLICATION_SESSIONS.pop(session_id, None) if session_id else None

    if not session_data:
        return page(
            "Logout error",
            "<p>No local session or ID token is available for logout.</p>",
        ), 400

    id_token = session_data["id_token"]
    logout_state = secrets.token_urlsafe(32)

    params = {
        "id_token_hint": id_token,
        "post_logout_redirect_uri": POST_LOGOUT_REDIRECT_URI,
        "state": logout_state,
    }

    response = make_response(
        redirect(END_SESSION_ENDPOINT + "?" + urlencode(params))
    )
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.set_cookie(
        LOGOUT_COOKIE,
        logout_state,
        max_age=300,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/",
    )

    print("[Day 10 Session] Local application session destroyed.")
    print("[Day 10 Session] Redirecting browser to Okta end-session endpoint.")
    return response


@app.get("/logged-out")
def logged_out():
    expected_state = request.cookies.get(LOGOUT_COOKIE)
    returned_state = request.args.get("state")
    state_ok = bool(
        expected_state
        and returned_state
        and secrets.compare_digest(expected_state, returned_state)
    )

    body = """
<p>Returned from the Okta end-session flow.</p>
<p>Logout state matched: <strong>%s</strong></p>
<p><a href="/">Return to application</a></p>
<p>
Try Sign in with Okta again. Whether a credential prompt appears depends on
the current Okta session and authentication policy.
</p>
""" % html.escape(str(state_ok))

    response = make_response(page("Day 10 Logged Out", body))
    response.delete_cookie(LOGOUT_COOKIE, path="/")
    return response


if __name__ == "__main__":
    print("Day 10 server-side session lifecycle app")
    print("Issuer: %s" % ISSUER)
    print("Sign-in redirect: %s" % REDIRECT_URI)
    print("Sign-out redirect: %s" % POST_LOGOUT_REDIRECT_URI)
    print("Open: http://localhost:%s" % PORT)
    print("")
    print("Training note:")
    print("- Local logout and Okta browser-session logout are separate routes.")
    print("- This sample does not revoke OAuth tokens during session logout.")
    app.run(host=HOST, port=PORT, debug=False)
