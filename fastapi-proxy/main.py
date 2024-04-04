# https://github.com/tiangolo/fastapi/issues/1788

import os

import httpx
from fastapi import FastAPI, Response
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import StreamingResponse

app = FastAPI(debug=True)

where = os.environ["WHERE"].strip("/") + "/"

print(f'{where=}')


@app.get("/x/{path:path}")
async def proxy(path: str, response: Response):
    redirect = where + path
    print(f'{redirect=}')
    async with httpx.AsyncClient() as client:
        proxy = await client.get(redirect, follow_redirects=True)
        response.body = proxy.content
        print(f'{len(response.body)=}')
        response.status_code = proxy.status_code
        return response


client = httpx.AsyncClient()


async def streaming_reverse_proxy(request: Request):
    redirect = where.strip("/") + request.url.path
    print(f'{redirect=}')
    url = httpx.URL(path=redirect, query=request.url.query.encode("utf-8"))
    print(f'{request.method} {url}')
    rp_req = client.build_request(
        request.method,
        redirect,
        content=request.stream(),
    )
    rp_resp = await client.send(rp_req, stream=True)
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )


app.add_route("/{path:path}", streaming_reverse_proxy, ["GET", "POST"])
