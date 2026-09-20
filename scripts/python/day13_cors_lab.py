#!/usr/bin/env python3
"""Day 13 local CORS evidence lab.

Runs:
    Browser page: http://localhost:5400
    API:          http://localhost:5401

Dependency:
    python -m pip install Flask

Default:
    The API does NOT allow the browser origin.

Enable the fix:
    PowerShell:
      $env:DAY13_CORS_ALLOW_ORIGIN="http://localhost:5400"

Then restart the script.

The browser request uses an Authorization header so the browser performs a
CORS preflight. The token is a harmless training string.
"""

import os
import threading

from flask import Flask, jsonify, make_response, request
from werkzeug.serving import make_server


UI_ORIGIN = "http://localhost:5400"
API_ORIGIN = "http://localhost:5401"
ALLOW_ORIGIN = os.environ.get("DAY13_CORS_ALLOW_ORIGIN", "").rstrip("/")

ui = Flask("day13_ui")
api = Flask("day13_api")


@ui.get("/")
def index():
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Day 13 CORS Evidence Lab</title>
</head>
<body>
  <h1>Day 13 CORS Evidence Lab</h1>
  <p>Page origin: <code>http://localhost:5400</code></p>
  <p>API origin: <code>http://localhost:5401</code></p>
  <button id="call">Call API from browser</button>
  <pre id="result">Open DevTools Network and Console before testing.</pre>

  <script>
    document.getElementById('call').addEventListener('click', async () => {
      const result = document.getElementById('result');
      result.textContent = 'Calling API...';

      try {
        const response = await fetch('http://localhost:5401/data', {
          method: 'GET',
          headers: {
            'Authorization': 'Bearer demo-token'
          }
        });

        const body = await response.json();
        result.textContent = JSON.stringify({
          browser_fetch_succeeded: true,
          http_status: response.status,
          body
        }, null, 2);
      } catch (error) {
        result.textContent = JSON.stringify({
          browser_fetch_succeeded: false,
          browser_error: String(error)
        }, null, 2);
      }
    });
  </script>
</body>
</html>"""


def add_cors_headers(response):
    if ALLOW_ORIGIN == UI_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = UI_ORIGIN
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization"
        response.headers["Vary"] = "Origin"
    return response


@api.route("/data", methods=["GET", "OPTIONS"])
def data():
    origin = request.headers.get("Origin")
    print(
        "[Day 13 CORS] method=%s origin=%s allow_origin=%s"
        % (request.method, origin, ALLOW_ORIGIN or "<not configured>")
    )

    if request.method == "OPTIONS":
        response = make_response("", 204)
        return add_cors_headers(response)

    auth = request.headers.get("Authorization", "")

    if auth != "Bearer demo-token":
        response = jsonify(
            {
                "error": "unauthorized",
                "server_received_request": True,
            }
        )
        response.status_code = 401
        return add_cors_headers(response)

    response = jsonify(
        {
            "message": "API received the real GET request.",
            "server_received_request": True,
        }
    )
    return add_cors_headers(response)


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__(daemon=True)
        self.server = make_server("localhost", port, app)

    def run(self):
        self.server.serve_forever()


if __name__ == "__main__":
    ui_server = ServerThread(ui, 5400)
    api_server = ServerThread(api, 5401)

    ui_server.start()
    api_server.start()

    print("Day 13 local CORS evidence lab")
    print("Browser page: %s" % UI_ORIGIN)
    print("API: %s" % API_ORIGIN)
    print(
        "Configured Access-Control-Allow-Origin: %s"
        % (ALLOW_ORIGIN or "<none>")
    )
    print("")
    print("Open DevTools, then open the browser page.")
    print("Press Ctrl+C to stop.")

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("")
        print("Stopping Day 13 CORS lab.")
