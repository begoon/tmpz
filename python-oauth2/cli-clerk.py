from __future__ import annotations

import http
import http.server
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import requests

secrets = json.loads(Path(f"secrets-{Path(__file__).name}.json").read_text())

if "create" in sys.argv:
    # https://clerk.com/docs/advanced-usage/clerk-idp
    response = requests.post(
        "https://api.clerk.com/v1/oauth_applications",
        headers={"Authorization": f"Bearer {secrets['secret_key']}"},
        json={
            "callback_url": "http://localhost:8000/callback",
            "name": "CLI",
            "scopes": "profile email",
        },
    )
    response.raise_for_status()
    settings = response.json()
    print("settings:", json.dumps(settings, indent=2))
    sys.exit()

PORT = 8000

settings = {
    "name": "CLI",
    "client_id": "?",
    "client_secret": "?",
    "scopes": "email profile",
    "callback_url": "http://localhost:8000/callback",
    "authorize_url": "?",
    "token_fetch_url": "?",
    "user_info_url": "?",
} | secrets


def authorise(settings: dict[str, str]) -> str:
    params = {
        "response_type": "code",
        "client_id": settings["client_id"],
        "redirect_uri": settings["callback_url"],
        "scope": settings["scopes"],
    }

    assert webbrowser.open(f"{settings["authorize_url"]}?{urlencode(params)}")

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
        "redirect_uri": settings["callback_url"],
        "code": code,
    }
    token_uri = settings["token_fetch_url"]

    response = requests.post(token_uri, data=params)
    response.raise_for_status()

    return response.json()


def get_userinfo(
    settings: dict[str, str],
    access_token: str,
) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(settings["user_info_url"], headers=headers)
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

    info = get_userinfo(settings, token["access_token"])
    print("user:", json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
