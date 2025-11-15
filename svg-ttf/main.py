import sys
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

# Bitmap layout
GLYPH_WIDTH_PIXELS = 6
GLYPH_HEIGHT_PIXELS = 8
NUM_GLYPHS = 256
BYTES_PER_GLYPH = GLYPH_HEIGHT_PIXELS
EXPECTED_FILE_SIZE = NUM_GLYPHS * BYTES_PER_GLYPH  # 2048 bytes

# SVG pixel size (purely visual)
SVG_PIXEL_SIZE = 10
SVG_WIDTH = GLYPH_WIDTH_PIXELS * SVG_PIXEL_SIZE
SVG_HEIGHT = GLYPH_HEIGHT_PIXELS * SVG_PIXEL_SIZE

# Sprite sheet layout
SPRITE_COLS = 16
SPRITE_ROWS = (NUM_GLYPHS + SPRITE_COLS - 1) // SPRITE_COLS

# Font metrics (TrueType units)
FONT_EM = 1000
FONT_PIXEL_SIZE = 100  # 1 bitmap pixel -> 100 font units
FONT_ASCENT = GLYPH_HEIGHT_PIXELS * FONT_PIXEL_SIZE  # 8*100 = 800
FONT_DESCENT = FONT_EM - FONT_ASCENT  # 200
GLYPH_ADVANCE = GLYPH_WIDTH_PIXELS * FONT_PIXEL_SIZE  # 6*100 = 600

SVG_BACKGROUND_COLOR = "black"
SVG_PIXEL_COLOR = "lightgreen"

UNICODE_OFFSET = 0x0100


def read_bitmap(path):
    data = Path(path).read_bytes()
    if len(data) != EXPECTED_FILE_SIZE:
        raise ValueError(
            f"Expected file size {EXPECTED_FILE_SIZE} bytes "
            f"(256 glyphs × 8 bytes), got {len(data)} bytes."
        )
    return data


def extract_glyph_bits(data, glyph_index):
    start = glyph_index * BYTES_PER_GLYPH
    rows = data[start : start + BYTES_PER_GLYPH]

    bits = []
    for row_byte in rows:
        row_bits = []
        for col in range(GLYPH_WIDTH_PIXELS):
            bit_index = 5 - col
            value = ((row_byte ^ 0xFF) >> bit_index) & 0x01
            row_bits.append(value)
        bits.append(row_bits)

    return bits  # bits[row][col]


def glyph_to_svg(glyph_bits):
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'shape-rendering="crispEdges" '
        f'width="{SVG_WIDTH}" height="{SVG_HEIGHT}" '
        f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'
    )
    parts.append(
        f'  <rect x="0" y="0" width="100%" height="100%" fill="{SVG_BACKGROUND_COLOR}" />'
    )

    for row in range(GLYPH_HEIGHT_PIXELS):
        for col in range(GLYPH_WIDTH_PIXELS):
            if glyph_bits[row][col]:
                x = col * SVG_PIXEL_SIZE
                y = row * SVG_PIXEL_SIZE
                parts.append(
                    f'  <rect x="{x}" y="{y}" width="{SVG_PIXEL_SIZE}" '
                    f'height="{SVG_PIXEL_SIZE}" fill="{SVG_PIXEL_COLOR}" />'
                )

    parts.append("</svg>")
    return "\n".join(parts)


def sprite_sheet_svg(all_glyph_bits):
    sheet_width = SPRITE_COLS * SVG_WIDTH
    sheet_height = SPRITE_ROWS * SVG_HEIGHT

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{sheet_width}" height="{sheet_height}" '
        f'viewBox="0 0 {sheet_width} {sheet_height}">'
    )
    parts.append(
        f'  <rect x="0" y="0" width="100%" height="100%" fill="{SVG_BACKGROUND_COLOR}" />'
    )

    for glyph_index, glyph_bits in enumerate(all_glyph_bits):
        gx = (glyph_index % SPRITE_COLS) * SVG_WIDTH
        gy = (glyph_index // SPRITE_COLS) * SVG_HEIGHT

        parts.append(f'  <g transform="translate({gx},{gy})">')
        for row in range(GLYPH_HEIGHT_PIXELS):
            for col in range(GLYPH_WIDTH_PIXELS):
                if glyph_bits[row][col]:
                    x = col * SVG_PIXEL_SIZE
                    y = row * SVG_PIXEL_SIZE
                    parts.append(
                        f'    <rect x="{x}" y="{y}" width="{SVG_PIXEL_SIZE}" '
                        f'height="{SVG_PIXEL_SIZE}" fill="{SVG_PIXEL_COLOR}" />'
                    )
        parts.append("  </g>")

    parts.append("</svg>")
    return "\n".join(parts)


def build_ttf_with_fonttools(all_glyph_bits, ttf_path):
    fb = FontBuilder(FONT_EM, isTTF=True)

    # 1) Glyph order
    glyph_order = [".notdef"] + [f"g{code:02X}" for code in range(NUM_GLYPHS)]
    fb.setupGlyphOrder(glyph_order)

    # 2) Character map: map 0x00..0xFF -> g00..gFF (with offset)
    cmap = {UNICODE_OFFSET + code: f"g{code:02X}" for code in range(NUM_GLYPHS)}
    fb.setupCharacterMap(cmap)

    # 3) Build glyphs and metrics
    glyphs = {}
    metrics = {}

    # .notdef: empty
    pen = TTGlyphPen(None)
    glyphs[".notdef"] = pen.glyph()
    metrics[".notdef"] = (GLYPH_ADVANCE, 0)

    for code in range(NUM_GLYPHS):
        name = f"g{code:02X}"
        bits = all_glyph_bits[code]

        pen = TTGlyphPen(None)

        # track leftmost used column to compute left sidebearing
        first_col = GLYPH_WIDTH_PIXELS
        any_on = False

        for row in range(GLYPH_HEIGHT_PIXELS):
            for col in range(GLYPH_WIDTH_PIXELS):
                if not bits[row][col]:
                    continue

                any_on = True
                if col < first_col:
                    first_col = col

                x0 = col * FONT_PIXEL_SIZE
                x1 = (col + 1) * FONT_PIXEL_SIZE

                # row 0 = top -> highest y
                y_bottom = (GLYPH_HEIGHT_PIXELS - 1 - row) * FONT_PIXEL_SIZE
                y_top = y_bottom + FONT_PIXEL_SIZE

                pen.moveTo((x0, y_bottom))
                pen.lineTo((x1, y_bottom))
                pen.lineTo((x1, y_top))
                pen.lineTo((x0, y_top))
                pen.closePath()

        glyphs[name] = pen.glyph()

        if any_on:
            # left sidebearing in font units, from origin to leftmost ink
            lsb = first_col * FONT_PIXEL_SIZE
        else:
            lsb = 0  # empty glyph

        metrics[name] = (GLYPH_ADVANCE, lsb)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)

    # 4) Basic vertical metrics
    fb.setupHorizontalHeader(ascent=FONT_ASCENT, descent=-FONT_DESCENT)

    # 5) OS/2 table
    fb.setupOS2(
        sTypoAscender=FONT_ASCENT,
        sTypoDescender=-FONT_DESCENT,
        sTypoLineGap=0,
        usWinAscent=FONT_ASCENT,
        usWinDescent=FONT_DESCENT,
        usWidthClass=5,  # Medium
        usWeightClass=400,  # Regular
    )

    # 6) Name table
    nameStrings = dict(
        familyName="Radio86RKPixel",
        styleName="Regular",
        uniqueFontIdentifier="Radio86RKPixel-Regular",
        fullName="Radio86RK Pixel Regular",
        psName="Radio86RKPixel-Regular",
        version="Version 1.0",
    )
    fb.setupNameTable(nameStrings)

    # 7) post table (monospaced-ish)
    fb.setupPost()

    fb.save(str(ttf_path))


def main(bitmap_path, svg_dir, ttf_path):
    data = read_bitmap(bitmap_path)

    out_dir = Path(svg_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_glyph_bits = []

    for glyph_index in range(NUM_GLYPHS):
        bits = extract_glyph_bits(data, glyph_index)
        all_glyph_bits.append(bits)

        svg_text = glyph_to_svg(bits)
        filename = f"glyph_{glyph_index:02x}.svg"
        (out_dir / filename).write_text(svg_text, encoding="utf-8")

    sprite_svg = sprite_sheet_svg(all_glyph_bits)
    (out_dir / "sprite.svg").write_text(sprite_svg, encoding="utf-8")

    build_ttf_with_fonttools(all_glyph_bits, Path(ttf_path))

    print(f"Generated {NUM_GLYPHS} SVGs in {out_dir}")
    print(f"Generated sprite: {out_dir / 'sprite.svg'}")
    print(f"Generated TTF: {ttf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <font_bitmap.bin> <output_svg_dir> <output_font.ttf>",
            file=sys.stderr,
        )
        sys.exit(1)

    bitmap_path = sys.argv[1]
    svg_dir = sys.argv[2]
    ttf_path = sys.argv[3]

    main(bitmap_path, svg_dir, ttf_path)
