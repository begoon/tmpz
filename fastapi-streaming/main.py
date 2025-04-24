import asyncio
import random
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

application = FastAPI()


class Tick(BaseModel):
    when: datetime
    n: int = 0


def random_time():
    return 0.5 + random.random() - 0.5


async def streamer() -> AsyncGenerator[str, None]:
    n = 0
    while True:
        n += 1
        tick = Tick(when=datetime.now(), n=n)
        yield tick.model_dump_json() + "\n"
        await asyncio.sleep(random_time())


@application.get("/stream", response_model=Tick)
async def stream() -> StreamingResponse:
    return StreamingResponse(streamer(), media_type="application/json")


async def sse_streamer() -> AsyncGenerator[str, None]:
    n = 0
    while True:
        n += 1
        tick = Tick(when=datetime.now(), n=n)
        yield "data: " + tick.model_dump_json() + "\n\n"
        await asyncio.sleep(random_time())


@application.get("/sse", response_model=Tick)
async def sse() -> StreamingResponse:
    return StreamingResponse(sse_streamer(), media_type="text/event-stream")


application.mount("/", StaticFiles(directory="pages", html=True))
