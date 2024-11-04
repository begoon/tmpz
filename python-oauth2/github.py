from __future__ import annotations

import http
import http.server
import json
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

import requests

PORT = 8000

secrets = json.loads(Path(f"secrets-{Path(__file__).name}.json").read_text())

settings = {
    "client_id": "?",
    "client_secret": "?",
    "auth_uri": "https://github.com/login/oauth/authorize",
    "token_uri": "https://github.com/login/oauth/access_token",
    "user_uri": "https://api.github.com/user",
    "email_uri": "https://api.github.com/user/emails",
    "redirect_uri": "http://localhost:8000/callback",
} | secrets


def authorise(settings: dict[str, str]) -> str:
    params = {
        "client_id": settings["client_id"],
        "redirect_uri": settings["redirect_uri"],
        "scope": "user:email",
    }

    assert webbrowser.open(f"{settings["auth_uri"]}?{urlencode(params)}")

    server = Server("localhost", PORT)
    server.handle_request()

    code = server.query_params["code"]
    assert code

    return code


def get_token(settings: dict[str, str], code: str) -> dict[str, Any]:
    token_url = settings["token_uri"]
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "code": code,
        "redirect_uri": settings["redirect_uri"],
    }
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def get_user_details(
    settings: dict[str, str],
    access_token: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    user_url = settings["user_uri"]
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/json",
    }
    user_response = requests.get(user_url, headers=headers)
    user_response.raise_for_status()
    user_data = user_response.json()

    email_url = settings["email_uri"]
    email_response = requests.get(email_url, headers=headers)
    email_response.raise_for_status()
    email_data = email_response.json()

    return user_data, email_data


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

    user_data, email_data = get_user_details(settings, token["access_token"])
    print(json.dumps(user_data, indent=2))
    print(json.dumps(email_data, indent=2))


if __name__ == "__main__":
    main()
