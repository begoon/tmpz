from typing import Any, Callable

DrawDetection = Callable[..., None]


def draw_template(
    image_path: str,
    template: dict[str, Any],
    draw_detection: DrawDetection,
    output: str = "result.jpg",
):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    draw_detection(draw, template["detection"])

    text = f"{template['detection']['confidence']:.4f}"
    font = ImageFont.load_default(size=20)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (image.width - tw - 10, image.height - th - 10),
        text,
        fill="lightskyblue",
        font=font,
    )

    image.save(output)
    print(f"saved {output}")


def draw_compare(
    path_a: str,
    path_b: str,
    template_a: dict[str, Any],
    template_b: dict[str, Any],
    similarity: float,
    draw_detection: DrawDetection,
    scale_detection: Callable[[dict[str, Any], float], dict[str, Any]],
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

    draw_detection(draw, scale_detection(template_a["detection"], scale_a))
    draw_detection(
        draw,
        scale_detection(template_b["detection"], scale_b),
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
