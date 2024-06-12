import json
import os

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import master.bot as bot
from application import settings


@csrf_exempt
def update(request: HttpRequest) -> JsonResponse | HttpResponse:
    if request.method == 'POST':
        if settings.DEBUG:
            print(f"{request.headers=}")

        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token != bot.SECRET_TOKEN:
            return HttpResponse("Unauthorized", status=401)

        if settings.DEBUG:
            print(f"{request.body=}")

        data = json.loads(request.body) if request.body else {}

        bot.update(data)

        return JsonResponse({})
    return HttpResponse("ha?")


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse(bot.health())


def env(request: HttpRequest) -> JsonResponse:
    return JsonResponse(dict(os.environ))
