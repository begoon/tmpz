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
    "scopes": ["openid", "profile", "email"],
    "audience": "https://{DOMAIN}/api/v2/",
    "userinfo_uri": "https://{DOMAIN}/userinfo",
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

    response = requests.post(token_uri, json=params)
    response.raise_for_status()

    return response.json()


def get_claims(token: str) -> dict[str, Any]:
    return jwt.decode(token, options={"verify_signature": False})


def get_userinfo(
    settings: dict[str, str],
    access_token: str,
) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(settings["userinfo_uri"], headers=headers)
    response.raise_for_status()
    return response.json()


def get_management_api_token(settings: dict[str, str]) -> str:
    params = {
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "audience": settings["audience"],
        "grant_type": "client_credentials",
    }
    token_uri = settings["token_uri"]

    response = requests.post(token_uri, json=params)
    response.raise_for_status()

    data = response.json()
    print("management token:", json.dumps(data, indent=2))

    token = data["access_token"]
    print("management token claims:", json.dumps(get_claims(token), indent=2))

    return token


def get_user_metadata(
    user_id: str,
    management_api_token: str,
) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {management_api_token}'}
    url = f"{settings['audience']}users/{user_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_user_roles(user_id: str, management_api_token: str) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {management_api_token}'}
    url = f"{settings['audience']}users/{user_id}/roles"
    response = requests.get(url, headers=headers)
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

    info = get_userinfo(settings, token["access_token"])
    print("user:", json.dumps(info, indent=2))

    management_api_token = get_management_api_token(settings)
    print("management_api_token:", json.dumps(management_api_token, indent=2))

    user_id = info["sub"]
    print("user_id:", user_id)

    user_metadata = get_user_metadata(user_id, management_api_token)
    print("user_metadata:", json.dumps(user_metadata, indent=2))

    roles = get_user_roles(user_id, management_api_token)
    print("roles:", json.dumps(roles, indent=2))


if __name__ == "__main__":
    main()
