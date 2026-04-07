from typing import Any, Callable, Coroutine, cast

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

RPC = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


def rpc(url: str) -> RPC:
    print(f"rankone = {url}")

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
    )
    async def inner(request: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=request,
                timeout=None,
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    return inner


async def version_string(rpc: RPC) -> dict[str, Any]:
    return await rpc({"versionString": {}})


async def compare_templates(
    rpc: RPC,
    a: dict[str, Any],
    b: dict[str, Any],
) -> float:
    request = {"compareTemplates": {"a": a, "b": b}}
    response = await rpc(request)
    assert "compareTemplates" in response, response
    return cast(float, response["compareTemplates"]["similarity"])
