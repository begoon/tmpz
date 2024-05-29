import json
import os

import azure.functions as func

import bot_sync as bot

wh = os.getenv("WH")
if wh:
    wh += "/bot"

bot.starter(wh)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health")
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {"status": "alive", "updated_at": os.getenv("UPDATED_AT", "?")}
        ),
        status_code=200,
        headers={"Content-Type": "application/json"},
    )


@app.route(route="bot")
def bot_(req: func.HttpRequest) -> func.HttpResponse:
    method = req.method

    if method != "POST":
        return func.HttpResponse("teapot expected", status_code=418)

    request_json = req.get_json()
    if not request_json:
        return func.HttpResponse("where is a teapot?", status_code=400)

    bot.update(request_json)
    return func.HttpResponse(status_code=200)
