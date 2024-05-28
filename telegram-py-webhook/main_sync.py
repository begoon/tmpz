import json
import logging
import pathlib
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, request

load_dotenv()

import bot_sync as bot  # noqa: E402

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

wh: str | None = None

wh_file = pathlib.Path("wh.json")
if wh_file.exists():
    with wh_file.open() as f:
        wh = json.load(f)["url"]
        logger.info("webhook %s", wh)


listener = Flask(__name__)


@listener.post("/bot")
def update() -> Response:
    request_ = request.get_json()
    bot.update(request_)
    return Response()


@listener.get("/health")
def health() -> dict[str, Any]:
    return bot.health()
