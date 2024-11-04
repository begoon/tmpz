from __future__ import annotations

import http
import http.server
import json
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import jwt
import requests

PORT = 8000

secrets = json.loads(Path(f"secrets-{Path(__file__).name}.json").read_text())

settings = {
    "domain": "?",
    "client_id": "?",
    "client_secret": "?",
    "auth_uri": "https://{DOMAIN}/authorize",
    "token_uri": "https://{DOMAIN}/oauth/token",
    "userinfo_uri": "https://{DOMAIN}/userinfo",
    "redirect_uris": ["http://localhost:8000/callback"],
    "scopes": ["openid", "profile", "email"],
    "audience": "https://{DOMAIN}/api/v2/",
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
        #
        "audience": secrets["audience"],
    }

    assert webbrowser.open(f"{secrets["auth_uri"]}?{urlencode(params)}")

    server = Server("localhost", PORT)
    server.handle_request()

    code = server.query_params["code"]
    assert code

    return code


def get_token(secrets: dict[str, str], code: str) -> dict[str, str]:
    params = {
        "grant_type": "authorization_code",
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "redirect_uri": secrets["redirect_uris"][0],
        "code": code,
    }
    token_uri = secrets["token_uri"]

    response = requests.post(token_uri, json=params)
    response.raise_for_status()

    return response.json()


def get_claims(token: str) -> dict[str, Any]:
    return jwt.decode(token, options={"verify_signature": False})


def get_userinfo(secrets: dict[str, str], access_token: str) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(secrets["userinfo_uri"], headers=headers)
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

    tokens = get_token(settings, code)
    print("tokens:", json.dumps(tokens, indent=2))

    claims = get_claims(tokens["id_token"])
    print("claims:", json.dumps(claims, indent=2))

    info = get_userinfo(settings, tokens["access_token"])
    print("user:", json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
