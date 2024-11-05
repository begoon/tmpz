from __future__ import annotations

import hashlib
import http
import http.server
import json
import os
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import jwt
import requests

PORT = 8000

secrets = json.loads(Path(f"secrets-{Path(__file__).name}.json").read_text())

settings = {
    "client_id": "?",
    "client_secret": "?",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "tokeninfo_uri": "https://www.googleapis.com/oauth2/v3/tokeninfo",
    "scopes": [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
    "redirect_uris": ["http://localhost:8000/auth"],
} | secrets

for name, value in settings.items():
    if "{DOMAIN}" in value:
        settings[name] = value.replace("{DOMAIN}", settings["domain"])


def authorise(secrets: dict[str, str]) -> str:
    params = {
        "response_type": "code",
        "client_id": secrets["client_id"],
        "redirect_uri": secrets["redirect_uris"][0],
        "scope": " ".join(secrets["scopes"]),
        "state": hashlib.sha256(os.urandom(1024)).hexdigest(),
        "access_type": "offline",
        "prompt": "consent",
    }

    assert webbrowser.open(f"{secrets["auth_uri"]}?{urlencode(params)}")

    server = Server("localhost", PORT)
    server.handle_request()

    assert (
        params["state"] == server.query_params["state"]
    ), f"{params['state']=} != {server.query_params['state']=}"

    code = server.query_params["code"]
    assert code

    return code


def get_token(settings: dict[str, str], code: str) -> dict[str, str]:
    params = {
        "grant_type": "authorization_code",
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "redirect_uri": settings["redirect_uris"][0],
        "code": code,
    }
    token_uri = settings["token_uri"]

    response = requests.post(token_uri, json=params)
    response.raise_for_status()

    return response.json()


def get_claims(token: str) -> dict[str, Any]:
    return jwt.decode(token, options={"verify_signature": False})


def check_access_token(
    settings: dict[str, str],
    access_token: str,
) -> dict[str, str]:
    url = f"{settings["tokeninfo_uri"]}?access_token={access_token}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def refresh_token(
    settings: dict[str, str],
    refresh_token: str,
) -> dict[str, str]:
    url = settings["token_uri"]
    params = {
        "grant_type": "refresh_token",
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "refresh_token": refresh_token,
    }
    response = requests.post(url, json=params)
    response.raise_for_status()
    return response.json()


class Handler(http.server.BaseHTTPRequestHandler):
    server: Server

    def do_GET(self):
        print(self.request, "\n", self.path)

        query_params = dict(parse_qsl(urlparse(self.path).query))
        print("query_params", json.dumps(query_params, indent=2))

        self.server.query_params = query_params

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(b"AUTHORISED")


class Server(http.server.HTTPServer):
    query_params: dict[str, str]

    def __init__(self, host, port):
        self.query_params = {}
        super().__init__((host, port), Handler)


def main():
    code = authorise(settings)

    token = get_token(settings, code)
    print("token:", json.dumps(token, indent=2))

    claims = get_claims(token["id_token"])
    print("claims:", json.dumps(claims, indent=2))

    token_info = check_access_token(settings, token["access_token"])
    print("id_token:", json.dumps(token_info, indent=2))

    if "refresh_token" in token:
        refreshed_token = refresh_token(settings, token["refresh_token"])
        print("refreshed_token:", json.dumps(refreshed_token, indent=2))

        refreshed_token_info = check_access_token(
            settings,
            refreshed_token["access_token"],
        )
        print(
            "refreshed id_token:",
            json.dumps(refreshed_token_info, indent=2),
        )

        claims = get_claims(refreshed_token["id_token"])
        print("claims:", json.dumps(claims, indent=2))


if __name__ == "__main__":
    main()
