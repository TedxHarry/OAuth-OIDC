#!/usr/bin/env python3
"""Small local HTTP server for the Day 2 OAuth/OIDC HTTP lab.

Uses only the Python standard library.

Run:
    python day02_http_lab_server.py

Then open:
    http://localhost:8000
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
import json
import os


HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))


def pretty_json(data):
    return json.dumps(data, indent=2).encode("utf-8")


class LabHandler(BaseHTTPRequestHandler):
    server_version = "Day2HttpLab/1.0"

    def send_json(self, status, data, headers=None):
        body = pretty_json(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, status, html, headers=None):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def request_summary(self, parsed):
        return {
            "method": self.command,
            "path": parsed.path,
            "query": parse_qs(parsed.query),
            "headers": {
                name: value
                for name, value in self.headers.items()
            },
        }

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_html(
                200,
                """<!doctype html>
<html>
<head><title>Day 2 HTTP Lab</title></head>
<body>
<h1>Day 2 HTTP Lab</h1>
<ul>
  <li><a href="/hello?name=Harish&topic=OAuth">GET with query parameters</a></li>
  <li><a href="/redirect">302 redirect</a></li>
  <li><a href="/set-cookie">Set a cookie</a></li>
  <li><a href="/show-cookie">Show received cookies</a></li>
  <li><a href="/protected">Protected endpoint without bearer token</a></li>
</ul>
<p>Use Postman for POST /form and for Authorization header tests.</p>
</body>
</html>""",
            )
            return

        if parsed.path == "/hello":
            self.send_json(200, self.request_summary(parsed))
            return

        if parsed.path == "/redirect":
            params = urlencode({
                "code": "demo-code",
                "state": "demo-state",
            })
            location = f"/callback?{params}"
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()
            return

        if parsed.path == "/callback":
            self.send_json(
                200,
                {
                    "message": "The browser reached the callback.",
                    **self.request_summary(parsed),
                },
            )
            return

        if parsed.path == "/set-cookie":
            self.send_json(
                200,
                {
                    "message": "Cookie sent to the browser.",
                    "next": "Open /show-cookie",
                },
                headers={
                    "Set-Cookie": "demo_session=abc123; HttpOnly; SameSite=Lax; Path=/"
                },
            )
            return

        if parsed.path == "/show-cookie":
            self.send_json(
                200,
                {
                    "cookie_header_received": self.headers.get("Cookie"),
                    **self.request_summary(parsed),
                },
            )
            return

        if parsed.path == "/protected":
            authorization = self.headers.get("Authorization")
            if authorization != "Bearer demo-token":
                self.send_json(
                    401,
                    {
                        "error": "invalid_or_missing_token",
                        "expected_for_lab": "Authorization: Bearer demo-token",
                        "received_authorization_header": authorization,
                    },
                    headers={
                        "WWW-Authenticate": 'Bearer realm="day2-lab"'
                    },
                )
                return

            self.send_json(
                200,
                {
                    "message": "Bearer token accepted.",
                    "authorization_header": authorization,
                },
            )
            return

        self.send_json(
            404,
            {
                "error": "not_found",
                "path": parsed.path,
            },
        )

    def do_POST(self):
        parsed = urlparse(self.path)

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        if parsed.path == "/form":
            decoded = raw_body.decode("utf-8", errors="replace")
            form_values = (
                parse_qs(decoded)
                if "application/x-www-form-urlencoded" in content_type
                else None
            )

            self.send_json(
                200,
                {
                    "method": self.command,
                    "path": parsed.path,
                    "content_type": content_type,
                    "raw_body": decoded,
                    "parsed_form_values": form_values,
                    "authorization_header": self.headers.get("Authorization"),
                },
            )
            return

        self.send_json(
            404,
            {
                "error": "not_found",
                "path": parsed.path,
            },
        )

    def log_message(self, format_string, *args):
        print(
            f"{self.client_address[0]} "
            f"{self.command} "
            f"{self.path} "
            f"{format_string % args}"
        )


def main():
    server = ThreadingHTTPServer((HOST, PORT), LabHandler)

    print(f"Day 2 HTTP lab server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
