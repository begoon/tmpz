from dotenv import load_dotenv
from flask import Flask, Response, request

load_dotenv()

import bot_ as bot  # noqa: E402

bot.starter()

listener = Flask(__name__)


@listener.post("/bot")
def update() -> Response:
    bot.update_(request.get_json())
    return Response()
