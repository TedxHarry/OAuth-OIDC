#!/usr/bin/env python3
"""Day 9 Employee API.

This API demonstrates a dedicated Employee API authorization boundary.

Protected endpoints:
    GET /api/employees -> requires employee.read
    GET /api/salary    -> requires salary.read

Dependencies:
    python -m pip install Flask requests "PyJWT[crypto]"

Required environment variables:
    OKTA_API_ISSUER
    OKTA_API_AUDIENCE
    OKTA_EXPECTED_CLIENT_ID

Expected Day 9 audience:
    api://employee-service

The API validates the access token before checking endpoint scopes.
department and groups are returned only as safe context. They are not used as
additional authorization requirements in this first design.
"""

import json
import os
import secrets

import jwt
import requests
from flask import Flask, g, jsonify, request
from jwt import PyJWKClient


HOST = "localhost"
PORT = 7000
REALM = "employee-api"

ISSUER = os.environ.get("OKTA_API_ISSUER", "").rstrip("/")
EXPECTED_AUDIENCE = os.environ.get("OKTA_API_AUDIENCE", "")
EXPECTED_CLIENT_ID = os.environ.get("OKTA_EXPECTED_CLIENT_ID", "")

if not ISSUER or not EXPECTED_AUDIENCE or not EXPECTED_CLIENT_ID:
    raise SystemExit(
        "Set OKTA_API_ISSUER, OKTA_API_AUDIENCE, and "
        "OKTA_EXPECTED_CLIENT_ID before starting the Day 9 API."
    )


def fetch_json(url):
    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


DISCOVERY_URL = ISSUER + "/.well-known/openid-configuration"
METADATA = fetch_json(DISCOVERY_URL)

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


def validate_access_token(token):
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
                    "sub",
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

    if claims.get("cid") != EXPECTED_CLIENT_ID:
        return None, "client_id", "unexpected_cid"

    scopes = claims.get("scp")

    if not isinstance(scopes, list) or not all(
        isinstance(scope, str) for scope in scopes
    ):
        return None, "scope_claim", "scp_not_string_array"

    groups = claims.get("groups")

    if groups is not None and (
        not isinstance(groups, list)
        or not all(isinstance(group, str) for group in groups)
    ):
        return None, "groups_claim", "groups_not_string_array"

    return claims, None, None


def authorize(required_scope):
    token, extraction_error = extract_bearer_token()

    if extraction_error == "missing":
        log_event("unauthorized", "bearer_token", "missing")
        return None, error_response(
            401,
            "unauthorized",
            "Bearer access token required.",
            bearer_challenge(),
        )

    if extraction_error == "malformed":
        log_event("invalid_token", "bearer_token", "malformed_header")
        return None, error_response(
            401,
            "invalid_token",
            "Bearer token format is invalid.",
            bearer_challenge(error="invalid_token"),
        )

    claims, stage, detail = validate_access_token(token)

    if claims is None:
        log_event("invalid_token", stage, detail)
        return None, error_response(
            401,
            "invalid_token",
            "Access token validation failed.",
            bearer_challenge(error="invalid_token"),
        )

    scopes = claims["scp"]

    if required_scope not in scopes:
        log_event(
            "insufficient_scope",
            "authorization",
            "required_scope=%s" % required_scope,
        )
        return None, error_response(
            403,
            "insufficient_scope",
            "The access token does not grant the required scope.",
            bearer_challenge(
                error="insufficient_scope",
                scope=required_scope,
            ),
        )

    log_event(
        "allowed",
        "authorization",
        "required_scope=%s" % required_scope,
    )
    return claims, None


def caller_context(claims):
    return {
        "sub": claims.get("sub"),
        "cid": claims.get("cid"),
        "scopes": claims.get("scp"),
        "department": claims.get("department"),
        "groups": claims.get("groups"),
    }


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
            "employee_scope": "employee.read",
            "salary_scope": "salary.read",
        }
    )


@app.get("/api/employees")
def employees():
    claims, failure = authorize("employee.read")

    if failure:
        return failure

    return jsonify(
        {
            "employees": [
                {
                    "id": "E1001",
                    "displayName": "Asha Patel",
                    "department": "Engineering",
                },
                {
                    "id": "E1002",
                    "displayName": "Marcus Lee",
                    "department": "Finance",
                },
            ],
            "caller": caller_context(claims),
            "authorization": {
                "required_scope": "employee.read",
                "decision": "allowed",
            },
            "correlation_id": g.correlation_id,
        }
    )


@app.get("/api/salary")
def salary():
    claims, failure = authorize("salary.read")

    if failure:
        return failure

    return jsonify(
        {
            "salaryRecords": [
                {
                    "employeeId": "E1001",
                    "annualSalary": 125000,
                    "currency": "USD",
                },
                {
                    "employeeId": "E1002",
                    "annualSalary": 118000,
                    "currency": "USD",
                },
            ],
            "caller": caller_context(claims),
            "authorization": {
                "required_scope": "salary.read",
                "decision": "allowed",
                "note": (
                    "department and groups are context only; "
                    "salary.read is the enforced permission"
                ),
            },
            "correlation_id": g.correlation_id,
        }
    )


if __name__ == "__main__":
    print("Day 9 Employee API")
    print("Issuer: %s" % ISSUER)
    print("Audience: %s" % EXPECTED_AUDIENCE)
    print("Expected client ID: %s" % EXPECTED_CLIENT_ID)
    print("Employee endpoint: http://localhost:%s/api/employees" % PORT)
    print("Salary endpoint: http://localhost:%s/api/salary" % PORT)
    print("")
    print("Authorization model:")
    print("- /api/employees requires employee.read")
    print("- /api/salary requires salary.read")
    print("- department/groups are context, not extra permission checks")
    print("- raw bearer tokens are never logged")
    app.run(host=HOST, port=PORT, debug=False)
