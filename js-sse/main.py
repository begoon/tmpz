import asyncio
import datetime

import fastapi
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

application = fastapi.FastAPI()


@application.get("/")
async def root():
    return FileResponse('index-py.html')


@application.get("/sse")
async def sse(request: fastapi.Request):
    async def ticks():
        id = 0
        while True:
            await asyncio.sleep(1)
            data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            yield {"event": "message", "id": id, "data": data}
            id += 1000

    return EventSourceResponse(ticks())
