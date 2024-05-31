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
    request_ = request.get_json()
    bot.update(request_)
    return Response()


@listener.get("/health")
def health() -> dict[str, Any]:
    return bot.health()
