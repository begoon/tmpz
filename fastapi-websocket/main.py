from fastapi import FastAPI
from starlette.websockets import WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    async for data in websocket.iter_text():
        await websocket.send_text(f"message text was: {data}")
        if data == "close":
            await websocket.close()
            break
        if data == "error":
            raise ValueError(data)
        if data == "1/0":
            1 / 0
    print(websocket.state)
