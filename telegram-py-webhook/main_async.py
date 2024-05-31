import logging
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Response

load_dotenv()

import bot_async  # noqa: E402

logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(listener: FastAPI):
    await bot_async.starter()
    yield
    await bot_async.finisher()


listener = FastAPI(lifespan=lifespan)


@listener.post("/bot")
async def update(request: dict[str, Any]) -> Response:
    await bot_async.update(request)
    return Response()


@listener.get("/health")
async def health() -> dict[str, Any]:
    return bot_async.health()
