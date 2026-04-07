import asyncio
import base64
import os
import sys
from pathlib import Path
from typing import Any, cast

from draw import draw_compare, draw_template
from rankone import RPC, compare_templates, rpc, version_string


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
    for keypoint in keypoints:
        if keypoint in det:
            px, py = ox + det[keypoint]["x"], oy + det[keypoint]["y"]
            draw.line([px - r, py - r, px + r, py + r], fill="white", width=2)
            draw.line([px - r, py + r, px + r, py - r], fill="white", width=2)


def _scale_detection(det: dict[str, Any], scale: float) -> dict[str, Any]:
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


async def main():
    r = rpc(os.environ["RANKONE_330"])
    print(await version_string(r))

    if len(sys.argv) < 2:
        return

    if len(sys.argv) < 3:
        template = await represent_face(r, Path(sys.argv[1]).read_bytes())
        draw_template(sys.argv[1], template, _draw_detection)
        return

    image_a = Path(sys.argv[1]).read_bytes()
    image_b = Path(sys.argv[2]).read_bytes()

    template_a = await represent_face(r, image_a)
    template_b = await represent_face(r, image_b)

    similarity = await compare_templates(r, template_a, template_b)
    print(f"similarity = {similarity}")
    draw_compare(
        sys.argv[1],
        sys.argv[2],
        template_a,
        template_b,
        similarity,
        _draw_detection,
        _scale_detection,
    )


if __name__ == "__main__":
    asyncio.run(main())
