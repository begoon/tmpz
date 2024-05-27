import logging
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Response

load_dotenv()

import bot  # noqa: E402

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(listener: FastAPI):
    await bot.starter()
    yield
    await bot.finisher()


listener = FastAPI(lifespan=lifespan)


@listener.post("/bot")
async def update(request: dict[str, Any]) -> Response:
    await bot.update(request)
    return Response()


@listener.get("/health")
async def health() -> dict[str, Any]:
    return bot.health()
