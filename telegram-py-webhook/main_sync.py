import logging
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, request

load_dotenv()

import bot_sync as bot  # noqa: E402

logger = logging.getLogger(__name__)

bot.starter()

listener = Flask(__name__)


@listener.post("/bot")
def update() -> Response:
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != bot.SECRET_TOKEN:
        return Response(status=403)

    request_ = request.get_json()
    bot.update(request_)
    return Response()


@listener.get("/health")
def health() -> dict[str, Any]:
    return bot.health()
