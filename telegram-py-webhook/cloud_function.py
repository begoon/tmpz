import os

import flask
import functions_framework

import bot_sync as bot

wh = os.getenv("WH")
if wh:
    wh += "/bot"

bot.starter(wh)


@functions_framework.http
def function_handler(request: flask.Request):
    method = request.method
    path = request.path

    if method == "GET" and "/health" in path:
        return bot.health()

    if method == "POST" and path == "/bot":
        request_json = request.get_json(silent=True)
        if request_json is None:
            return {"error": "invalid json"}
        print(request_json)
        bot.update(request_json)
        return {}

    return ('Ha?', 418)
