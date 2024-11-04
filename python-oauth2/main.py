from __future__ import annotations

import base64
import hashlib
import http
import http.server
import json
import logging
import os
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import jwt
import requests

PORT = 8000

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def authorise(secrets: dict[str, str]) -> dict[str, str]:
    redirect_uri = f"{secrets['redirect_uris'][0]}"
    params = {
        "response_type": "code",
        "client_id": secrets["client_id"],
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": hashlib.sha256(os.urandom(1024)).hexdigest(),
        "access_type": "offline",
        "prompt": "none",  # or "consent"
    }
    url = f"{secrets['auth_uri']}?{urlencode(params)}"
    assert webbrowser.open(url)

    server = Server("localhost", 8000)
    server.handle_request()

    assert (
        params["state"] == server.query_params["state"]
    ), f"{params['state']=} != {server.query_params['state']=}"

    code = server.query_params["code"]
    params = {
        "grant_type": "authorization_code",
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "redirect_uri": redirect_uri,
        "code": code,
    }

    with requests.post(
        secrets["token_uri"],
        data=params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as response:
        response.raise_for_status()
        return response.json()


def check_access_token(access_token: str) -> dict[str, str]:
    with requests.get(
        f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as response:
        response.raise_for_status()
        return response.json()


def refresh_token(
    secrets: dict[str, str],
    refresh_token: str,
) -> dict[str, str]:
    params = {
        "grant_type": "refresh_token",
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "refresh_token": refresh_token,
    }
    with requests.post(
        secrets["token_uri"],
        data=params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as response:
        response.raise_for_status()
        return response.json()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path, self.request)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        query = dict(
            [
                (k, ",".join(v))
                for k, v in parse_qs(self.path.split("?")[1]).items()
            ]
        )
        print("query", json.dumps(query, indent=2))

        self.server.query_params = query

        self.wfile.write(b"AUTHORISED")


class Server(http.server.HTTPServer):
    def __init__(self, host, port):
        super().__init__((host, port), Handler)


def main():
    secrets = json.loads(Path("oauth2-secrets.json").read_text())
    tokens = authorise(secrets)
    print("tokens:", json.dumps(tokens, indent=2))

    claims = jwt.decode(
        tokens["id_token"],
        options={"verify_signature": False},
    )
    print(f"{claims=}")

    token_info = check_access_token(tokens["access_token"])
    print("id_token:", json.dumps(token_info, indent=2))

    if "refresh_token" in tokens:
        refreshed_tokens = refresh_token(secrets, tokens["refresh_token"])
        print("refreshed_tokens:", json.dumps(refreshed_tokens, indent=2))
        refreshed_token_info = check_access_token(
            refreshed_tokens["access_token"]
        )
        print(
            "refreshed id_token:",
            json.dumps(refreshed_token_info, indent=2),
        )


if __name__ == "__main__":
    main()
