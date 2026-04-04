import asyncio
import base64
import os
import sys
from pathlib import Path
from typing import Any, Callable, Coroutine, cast

import httpx

RPC = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


def rankone(url: str) -> RPC:
    print(f"rankone = {url}")

    async def inner(request: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=request,
                    timeout=None,
                )
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            print(f"rankone error: {e}, url: {e.request.url}")

    return inner


async def version_string(rpc: RPC) -> dict[str, Any]:
    return await rpc({"versionString": {}})


async def represent_face(rpc: RPC, image: bytes) -> dict[str, Any]:
    request = {
        "represent": {
            "image": base64.b64encode(image).decode(),
            "algorithmOptions": [
                "ROC_FACE_DETECTION",
                "ROC_FACE_BALANCED_REPRESENTATION",
            ],
            "minQuality": -4.0,
            "minSize": 20,
            "falseDetectionRate": 0.02,
            "k": 1,
        },
    }
    response = await rpc(request)
    assert "represent" in response, response

    assert len(response["represent"]["templates"]) == 1, response
    template = response["represent"]["templates"][0]

    if "fv" in template:
        fv = base64.b64decode(template["fv"])
        print(f"fv {len(fv)=}")

    return cast(dict[str, Any], template)


async def compare_templates(
    rpc: RPC,
    a: dict[str, Any],
    b: dict[str, Any],
) -> float:
    request = {"compareTemplates": {"a": a, "b": b}}
    response = await rpc(request)
    assert "compareTemplates" in response, response
    return cast(float, response["compareTemplates"]["similarity"])


def rpc_from_env():
    return rankone(os.environ["RANKONE"])


async def main():
    rpc = rpc_from_env()
    print(await version_string(rpc))

    if len(sys.argv) < 2:
        return

    if len(sys.argv) < 3:
        template = await represent_face(rpc, Path(sys.argv[1]).read_bytes())
        print(template)
        return

    image_a = Path(sys.argv[1]).read_bytes()
    image_b = Path(sys.argv[2]).read_bytes()

    template_a = await represent_face(rpc, image_a)
    template_b = await represent_face(rpc, image_b)

    similarity = await compare_templates(rpc, template_a, template_b)

    print(f"similarity = {similarity}")


if __name__ == "__main__":
    asyncio.run(main())
