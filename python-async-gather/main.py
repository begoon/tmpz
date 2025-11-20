import asyncio
import random
from typing import Set

from fastapi import FastAPI, WebSocket

application = FastAPI()


@application.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("ws/connected")

    stop_event = asyncio.Event()
    active_tasks: Set[asyncio.Task] = set()

    async def process_task(data: int) -> bool:
        success = random.random() < 0.1
        print(f"[worker] {data} finished, {success=}")
        if not success:
            await asyncio.sleep(random.uniform(0.5, 2.0))
        return success

    async def worker_wrapper(data: int):
        try:
            success = await process_task(data)
            if success and not stop_event.is_set():
                print(f"SUCCESS on {data}, stop processing")
                stop_event.set()
        except asyncio.CancelledError:
            print(f"[worker] {data}: cancelled")
            raise
        finally:
            me = asyncio.current_task()
            if me in active_tasks:
                active_tasks.discard(me)

    await websocket.accept()

    while stop_event.is_set() is False:
        request = await websocket.receive_text()

        t = asyncio.create_task(worker_wrapper(int(request)))
        active_tasks.add(t)

        finished = {t for t in active_tasks if t.done()}
        active_tasks -= finished

    print("cancel still active workers:", len(active_tasks))
    for t in active_tasks:
        t.cancel()

    if active_tasks:
        await asyncio.gather(*active_tasks, return_exceptions=True)

    print("DONE")

    await websocket.close()
