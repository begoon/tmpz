import json
import os

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from application import settings


@csrf_exempt
def callback(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        data = json.loads(request.body) if request.body else {}
        return JsonResponse(
            {"message": "ok", "data": data, "headers": dict(request.headers)}
        )
    return JsonResponse({"message": "ha?"})


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "alive", "version": settings.VERSION})


def env(request: HttpRequest) -> JsonResponse:
    return JsonResponse(dict(os.environ))
