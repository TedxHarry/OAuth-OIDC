#!/usr/bin/env python3
"""Local callback receiver for the Day 3 Authorization Code + PKCE lab.

Run:
    python scripts/python/day03_pkce_callback_server.py

Register this redirect URI in the Okta SPA app:
    http://localhost:8000/callback

The server only displays the callback parameters. It does not exchange the
authorization code for tokens.
"""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "127.0.0.1"
PORT = 8000


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Use /callback for the Day 3 lab.")
            return

        params = parse_qs(parsed.query)

        code = params.get("code", [""])[0]
        state = params.get("state", [""])[0]
        error = params.get("error", [""])[0]
        error_description = params.get("error_description", [""])[0]

        print("\nDay 3 callback received")
        print(f"state={state}")

        if code:
            print("authorization_code_received=yes")
            print("Do not share the live authorization code.")
        if error:
            print(f"error={error}")
            print(f"error_description={error_description}")

        body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Day 3 PKCE Callback</title>
</head>
<body>
  <h1>Day 3 PKCE Callback</h1>
  <p>The browser reached the registered callback.</p>

  <h2>Returned state</h2>
  <pre>{escape(state)}</pre>

  <h2>Authorization code</h2>
  <pre>{escape(code)}</pre>

  <h2>Error</h2>
  <pre>{escape(error)}</pre>

  <h2>Error description</h2>
  <pre>{escape(error_description)}</pre>

  <p>Compare the returned state with the state generated before the authorization request.</p>
  <p>If a code is present, copy it only into your local Postman token request. Do not share it.</p>
</body>
</html>"""

        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format_string, *args):
        print(f"{self.client_address[0]} {self.command} {urlparse(self.path).path}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), CallbackHandler)

    print(f"Day 3 callback server running on http://localhost:{PORT}")
    print("Registered redirect URI should be:")
    print(f"http://localhost:{PORT}/callback")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping callback server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
