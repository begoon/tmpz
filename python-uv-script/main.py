#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["fastapi", "httpx", "uvicorn" ]
# ///
import asyncio
import os
import signal
from typing import Any

import fastapi
import httpx
import uvicorn

application = fastapi.FastAPI()


@application.get("/")
async def _() -> dict[str, Any]:
    return {"status": "ha?"}


async def listener():
    config = uvicorn.Config("main:application", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def make_request():
    await asyncio.sleep(0.5)
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/")
        print(response.json())


async def main():
    async with asyncio.TaskGroup() as tasks:
        server = tasks.create_task(listener())
        client = tasks.create_task(make_request())

        await asyncio.wait(
            [server, client],
            return_when=asyncio.FIRST_COMPLETED,
        )
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exiting...")
