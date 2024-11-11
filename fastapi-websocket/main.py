import traceback
from fastapi import FastAPI, WebSocketDisconnect
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

@app.websocket("/wsx")
async def websocket_endpoint(websocket: WebSocket) -> None:
    print("CONNECTED")  
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"message text was: {data}")
            if data == "close":
                await websocket.close()
                break
            if data == "error":
                1 / 0
    except WebSocketDisconnect as e:
        print(f"WS/SOCKET DISCONNECTED {e.code=} {e.reason=}")
    except Exception as e:
        print(f"EXCEPTION {e=} {websocket.client_state=}")
        await websocket.send_text(f"error: {e}")
        await websocket.close(code=1011, reason='unhandled websocket exception')
    finally:
        print("DISCONNECTED")
