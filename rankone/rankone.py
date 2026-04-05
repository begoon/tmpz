import asyncio
import base64
import os
import sys
from pathlib import Path
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


def rankone(url: str) -> RPC:
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


def _draw_detection(draw, det: dict[str, Any], ox: float = 0, oy: float = 0):
    cx, cy, w, h = det["x"], det["y"], det["width"], det["height"]
    x0, y0 = ox + cx - w / 2, oy + cy - h / 2
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline="lightskyblue", width=2)

    keypoints = [
        "leftEye",
        "rightEye",
        "nose",
        "rightMouthCorner",
        "leftMouthCorner",
        "chin",
    ]
    r = 5
    for kp in keypoints:
        if kp in det:
            px, py = ox + det[kp]["x"], oy + det[kp]["y"]
            draw.line([px - r, py - r, px + r, py + r], fill="white", width=2)
            draw.line([px - r, py + r, px + r, py - r], fill="white", width=2)


def draw_template(
    image_path: str,
    template: dict[str, Any],
    output: str = "result.jpg",
):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    _draw_detection(draw, template["detection"])

    text = f"{template['detection']['confidence']:.4f}"
    font = ImageFont.load_default(size=20)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (img.width - tw - 10, img.height - th - 10),
        text,
        fill="lightskyblue",
        font=font,
    )

    img.save(output)
    print(f"saved {output}")


def draw_compare(
    path_a: str,
    path_b: str,
    template_a: dict[str, Any],
    template_b: dict[str, Any],
    similarity: float,
    output: str = "result.jpg",
):
    from PIL import Image, ImageDraw, ImageFont

    img_a = Image.open(path_a)
    img_b = Image.open(path_b)

    max_h = max(img_a.height, img_b.height)
    scale_a = max_h / img_a.height
    scale_b = max_h / img_b.height
    if img_a.height != max_h:
        img_a = img_a.resize((int(img_a.width * scale_a), max_h))
    if img_b.height != max_h:
        img_b = img_b.resize((int(img_b.width * scale_b), max_h))

    result = Image.new("RGB", (img_a.width + img_b.width, max_h))
    result.paste(img_a, (0, 0))
    result.paste(img_b, (img_a.width, 0))

    draw = ImageDraw.Draw(result)

    def scaled_detection(det: dict[str, Any], scale: float) -> dict[str, Any]:
        out = dict(det)
        for key in ["x", "y", "width", "height"]:
            out[key] = det[key] * scale
        for keypoint in [
            "leftEye",
            "rightEye",
            "nose",
            "rightMouthCorner",
            "leftMouthCorner",
            "chin",
        ]:
            if keypoint in det:
                out[keypoint] = {
                    "x": det[keypoint]["x"] * scale,
                    "y": det[keypoint]["y"] * scale,
                }
        return out

    _draw_detection(draw, scaled_detection(template_a["detection"], scale_a))
    _draw_detection(
        draw,
        scaled_detection(template_b["detection"], scale_b),
        ox=img_a.width,
    )

    font = ImageFont.load_default(size=24)
    text = f"similarity = {similarity:.4f}"
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (result.width - tw - 10, result.height - th - 10),
        text,
        fill="lightskyblue",
        font=font,
    )

    result.save(output)
    print(f"saved {output}")


def rpc_from_env():
    return rankone(os.environ["RANKONE"])


async def main():
    rpc = rpc_from_env()
    print(await version_string(rpc))

    if len(sys.argv) < 2:
        return

    if len(sys.argv) < 3:
        template = await represent_face(rpc, Path(sys.argv[1]).read_bytes())
        draw_template(sys.argv[1], template)
        return

    image_a = Path(sys.argv[1]).read_bytes()
    image_b = Path(sys.argv[2]).read_bytes()

    template_a = await represent_face(rpc, image_a)
    template_b = await represent_face(rpc, image_b)

    similarity = await compare_templates(rpc, template_a, template_b)
    print(f"similarity = {similarity}")
    draw_compare(sys.argv[1], sys.argv[2], template_a, template_b, similarity)


if __name__ == "__main__":
    asyncio.run(main())
