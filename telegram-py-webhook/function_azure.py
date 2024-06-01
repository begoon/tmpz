import json

import azure.functions as func

import bot as bot

bot.starter()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health")
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(bot.health()),
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
