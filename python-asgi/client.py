import asyncio

import httpx


async def main():
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:8000')
        async for chunk in response.aiter_bytes():
            print(chunk.decode(), end='')


asyncio.run(main())
