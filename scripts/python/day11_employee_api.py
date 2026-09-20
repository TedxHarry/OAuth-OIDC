#!/usr/bin/env python3
"""Day 11 machine-to-machine Employee API endpoint.

Protected endpoint:
    GET /api/service-report

Required scope:
    employee.report.read

Dependencies:
    python -m pip install Flask requests "PyJWT[crypto]"

Required environment variables:
    OKTA_API_ISSUER
    OKTA_API_AUDIENCE
    OKTA_EXPECTED_SERVICE_CLIENT_ID

Optional:
    DAY11_REQUIRED_SCOPE
        Defaults to employee.report.read.
        The lab temporarily changes this value to prove a 403 path.

Important:
- This endpoint expects a Client Credentials access token.
- It validates the service client through cid.
- It does not require a user-specific uid claim.
- Raw bearer tokens are never logged.
"""

import json
import os
import secrets

import jwt
import requests
from flask import Flask, g, jsonify, request
from jwt import PyJWKClient


HOST = "localhost"
PORT = 7100
REALM = "employee-service-api"

ISSUER = os.environ.get("OKTA_API_ISSUER", "").rstrip("/")
EXPECTED_AUDIENCE = os.environ.get("OKTA_API_AUDIENCE", "")
EXPECTED_SERVICE_CLIENT_ID = os.environ.get(
    "OKTA_EXPECTED_SERVICE_CLIENT_ID",
    "",
)
REQUIRED_SCOPE = os.environ.get(
    "DAY11_REQUIRED_SCOPE",
    "employee.report.read",
)

if not ISSUER or not EXPECTED_AUDIENCE or not EXPECTED_SERVICE_CLIENT_ID:
    raise SystemExit(
        "Set OKTA_API_ISSUER, OKTA_API_AUDIENCE, and "
        "OKTA_EXPECTED_SERVICE_CLIENT_ID before starting the Day 11 API."
    )


def fetch_json(url):
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


METADATA = fetch_json(ISSUER + "/.well-known/openid-configuration")

if METADATA.get("issuer") != ISSUER:
    raise SystemExit(
        "Discovery issuer mismatch. Expected %r, got %r."
        % (ISSUER, METADATA.get("issuer"))
    )

JWKS_URI = METADATA.get("jwks_uri")

if not JWKS_URI:
    raise SystemExit("Discovery metadata did not contain jwks_uri.")

JWK_CLIENT = PyJWKClient(JWKS_URI)

app = Flask(__name__)


def log_event(result, stage, detail=None):
    message = {
        "correlation_id": g.correlation_id,
        "path": request.path,
        "result": result,
        "stage": stage,
    }

    if detail:
        message["detail"] = detail

    print(json.dumps(message, sort_keys=True))


def bearer_challenge(error=None, scope=None):
    parts = ['Bearer realm="%s"' % REALM]

    if error:
        parts.append('error="%s"' % error)

    if scope:
        parts.append('scope="%s"' % scope)

    return ", ".join(parts)


def error_response(status, error, message, challenge):
    response = jsonify(
        {
            "error": error,
            "message": message,
            "correlation_id": g.correlation_id,
        }
    )
    response.status_code = status
    response.headers["WWW-Authenticate"] = challenge
    response.headers["Cache-Control"] = "no-store"
    return response


def extract_bearer_token():
    value = request.headers.get("Authorization", "")

    if not value:
        return None, "missing"

    parts = value.split(None, 1)

    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        return None, "malformed"

    return parts[1].strip(), None


def validate_service_access_token(token):
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        return None, "jwt_header", type(exc).__name__

    if header.get("alg") != "RS256":
        return None, "algorithm", "expected_RS256"

    if not header.get("kid"):
        return None, "kid", "missing_kid"

    try:
        signing_key = JWK_CLIENT.get_signing_key_from_jwt(token)
    except Exception as exc:
        return None, "jwks_key_resolution", type(exc).__name__

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=EXPECTED_AUDIENCE,
            issuer=ISSUER,
            leeway=60,
            options={
                "require": [
                    "iss",
                    "aud",
                    "iat",
                    "exp",
                    "cid",
                    "scp",
                ],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        return None, "expiration", type(exc).__name__
    except jwt.InvalidAudienceError as exc:
        return None, "audience", type(exc).__name__
    except jwt.InvalidIssuerError as exc:
        return None, "issuer", type(exc).__name__
    except jwt.InvalidSignatureError as exc:
        return None, "signature", type(exc).__name__
    except jwt.ImmatureSignatureError as exc:
        return None, "time_claim", type(exc).__name__
    except jwt.MissingRequiredClaimError as exc:
        return None, "required_claim", str(exc.claim)
    except jwt.PyJWTError as exc:
        return None, "jwt_validation", type(exc).__name__

    if claims.get("cid") != EXPECTED_SERVICE_CLIENT_ID:
        return None, "client_id", "unexpected_cid"

    scopes = claims.get("scp")

    if not isinstance(scopes, list) or not all(
        isinstance(scope, str) for scope in scopes
    ):
        return None, "scope_claim", "scp_not_string_array"

    return claims, None, None


@app.before_request
def create_correlation_id():
    g.correlation_id = secrets.token_hex(8)


@app.after_request
def add_correlation_header(response):
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "issuer": ISSUER,
            "audience": EXPECTED_AUDIENCE,
            "expected_service_client_id": EXPECTED_SERVICE_CLIENT_ID,
            "required_scope": REQUIRED_SCOPE,
        }
    )


@app.get("/api/service-report")
def service_report():
    token, extraction_error = extract_bearer_token()

    if extraction_error == "missing":
        log_event("unauthorized", "bearer_token", "missing")
        return error_response(
            401,
            "unauthorized",
            "Bearer access token required.",
            bearer_challenge(),
        )

    if extraction_error == "malformed":
        log_event("invalid_token", "bearer_token", "malformed_header")
        return error_response(
            401,
            "invalid_token",
            "Bearer token format is invalid.",
            bearer_challenge(error="invalid_token"),
        )

    claims, stage, detail = validate_service_access_token(token)

    if claims is None:
        log_event("invalid_token", stage, detail)
        return error_response(
            401,
            "invalid_token",
            "Service access-token validation failed.",
            bearer_challenge(error="invalid_token"),
        )

    scopes = claims["scp"]

    if REQUIRED_SCOPE not in scopes:
        log_event(
            "insufficient_scope",
            "authorization",
            "required_scope=%s" % REQUIRED_SCOPE,
        )
        return error_response(
            403,
            "insufficient_scope",
            "The service access token does not grant the required scope.",
            bearer_challenge(
                error="insufficient_scope",
                scope=REQUIRED_SCOPE,
            ),
        )

    log_event(
        "allowed",
        "authorization",
        "required_scope=%s" % REQUIRED_SCOPE,
    )

    return jsonify(
        {
            "report": {
                "generatedFor": "nightly-employee-reporting",
                "employeeCount": 2,
                "departments": {
                    "Engineering": 1,
                    "Finance": 1,
                },
            },
            "caller": {
                "cid": claims.get("cid"),
                "scopes": scopes,
                "uid_present": "uid" in claims,
                "sub_present": "sub" in claims,
            },
            "authorization": {
                "required_scope": REQUIRED_SCOPE,
                "decision": "allowed",
            },
            "correlation_id": g.correlation_id,
        }
    )


if __name__ == "__main__":
    print("Day 11 machine-to-machine Employee API")
    print("Issuer: %s" % ISSUER)
    print("Audience: %s" % EXPECTED_AUDIENCE)
    print("Expected service client ID: %s" % EXPECTED_SERVICE_CLIENT_ID)
    print("Required scope: %s" % REQUIRED_SCOPE)
    print("Report endpoint: http://localhost:%s/api/service-report" % PORT)
    print("")
    print("Machine identity note:")
    print("- The API requires the expected service cid.")
    print("- It does not require a human uid.")
    print("- Raw bearer tokens are never logged.")
    app.run(host=HOST, port=PORT, debug=False)
