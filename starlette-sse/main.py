import asyncio
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

MESSAGE_STREAM_DELAY = 1  # second
MESSAGE_STREAM_RETRY_TIMEOUT = 15000  # milisecond
app = FastAPI()

messages = asyncio.Queue()

@app.get('/', response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Message Stream</title>
        </head>
        <body>
            <h1>Message Stream</h1>
            <div id="message-stream"></div>
            <script>
                const messageStream = new EventSource('/stream');
                messageStream.onmessage = (event) => {
                    const messageStreamDiv = document.getElementById('message-stream');
                    messageStreamDiv.innerHTML += event.data + '<br>';
                };
            </script>
        </body>
    </html>
    """

@app.get('/stream', response_class=EventSourceResponse)
async def message_stream(request: Request):
    def new_message() -> str | None:
        if not messages.empty():
            return messages.get_nowait()
        return None
    async def event_generator():
        data = ["Hello", "World", "How", "Are", "You", "Doing", "Today", "?"]
        for s in data:
            messages.put_nowait(s)
        print("client connected")
        while True:
            if await request.is_disconnected():
                print("client disconnected")
                break
            if (message := new_message()):
                yield {
                        "event": "message",
                        "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                        "data": f"data: {message}"
                        # "id": "message_id",
                }
            await asyncio.sleep(MESSAGE_STREAM_DELAY)
    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
