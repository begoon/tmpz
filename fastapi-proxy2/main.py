from typing import Iterable

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

UPSTREAM = "http://localhost:9000"

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    filtered: dict[str, str] = {}
    for header, value in headers:
        if header.lower() in HOP_BY_HOP_HEADERS:
            continue
        filtered[header] = value
    return filtered


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy(path: str, request: Request):
    target = UPSTREAM.rstrip("/")
    path = "/" + path
    query = request.url.query
    upstream_url = f"{target}{path}" + (f"?{query}" if query else "")
    print(f"-> proxying request to: {upstream_url}")

    headers = filter_headers(request.headers.items())

    # typical proxy headers (optional)
    if request.client and request.client.host:
        prior = headers.get("x-forwarded-for")
        headers["x-forwarded-for"] = (
            f"{prior}, {request.client.host}".strip(", ")
            if prior
            else request.client.host
        )
    headers["x-forwarded-proto"] = request.url.scheme
    headers["x-forwarded-host"] = request.headers.get("host", "")

    async def body_iter():
        async for chunk in request.stream():
            yield chunk

    client = httpx.AsyncClient(follow_redirects=False, timeout=None)

    # IMPORTANT: keep the *context manager* so we can close it later
    stream_content_manager = client.stream(
        method=request.method,
        url=upstream_url,
        headers=headers,
        content=body_iter(),
    )

    upstream = await stream_content_manager.__aenter__()

    # capture metadata now (before returning), while the stream is open
    response_headers = filter_headers(upstream.headers.items())
    status_code = upstream.status_code
    media_type = upstream.headers.get("content-type")

    async def upstream_iter():
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            # close the stream + client even if the downstream disconnects
            await stream_content_manager.__aexit__(None, None, None)
            await client.aclose()

    return StreamingResponse(
        upstream_iter(),
        status_code=status_code,
        headers=response_headers,
        media_type=media_type,
    )
