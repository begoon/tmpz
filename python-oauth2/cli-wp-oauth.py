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
    "auth_uri": "https://{DOMAIN}/oauth/authorize",
    "token_uri": "https://{DOMAIN}/oauth/token",
    "scopes": ["basic"],
    "audience": "https://{DOMAIN}/api/v2/",
    "userinfo_uri": "https://{DOMAIN}/oauth/me",
    "redirect_uris": ["http://localhost:8000/callback"],
} | secrets


for name, value in settings.items():
    if "{DOMAIN}" in value:
        settings[name] = value.replace("{DOMAIN}", settings["domain"])


def authorise(settings: dict[str, str]) -> str:
    params = {
        "response_type": "code",
        "client_id": settings["client_id"],
        "redirect_uri": settings["redirect_uris"][0],
        "scope": " ".join(settings["scopes"]),
        "audience": settings["audience"],
    }

    assert webbrowser.open(f"{settings["auth_uri"]}?{urlencode(params)}")

    server = Server("localhost", PORT)
    server.handle_request()

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

    print("params:", json.dumps(params, indent=2, ensure_ascii=False))
    print("token_uri:", token_uri)
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
        print(
            "query_params",
            json.dumps(
                query_params,
                indent=2,
                ensure_ascii=False,
            ),
        )

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
    print("token:", json.dumps(token, indent=2, ensure_ascii=False))

    claims = get_claims(token["id_token"])
    print("claims:", json.dumps(claims, indent=2, ensure_ascii=False))

    info = get_userinfo(settings, token["access_token"])
    print("user:", json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
