import asyncio

from websockets.server import serve


async def echo(websocket):
    async for message in websocket:
        msg = f"received {len(message)} bytes"
        print(msg)
        await websocket.send(msg)


MAX_SIZE = 10 * 1024 * 1024 + 1024


async def main():
    async with serve(echo, "localhost", 3000, max_size=MAX_SIZE):
        await asyncio.Future()


asyncio.run(main())
