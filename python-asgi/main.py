import asyncio


async def app(scope, receive, send):
    assert scope['type'] == 'http'
    print(scope)
    client = str(scope['client'])
    await send(
        {
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
                [b'X-Content-Type-Options', b'nosniff'],
            ],
        }
    )
    chunks: list[str] = ['dial', 'from', client, '!']
    for chunk in chunks:
        chunk = chunk + '\n'
        await send(
            {
                'type': 'http.response.body',
                'body': chunk.encode(),
                'more_body': True,
            }
        )
        print('sent chunk:', chunk.strip())
        await asyncio.sleep(1)
    await send({'type': 'http.response.body', 'body': b''})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)
