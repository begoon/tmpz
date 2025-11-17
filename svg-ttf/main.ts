#!/usr/bin/env ts-node

import * as fs from "node:fs";
import * as path from "node:path";
import * as opentype from "opentype.js";

// Bitmap layout
const GLYPH_WIDTH_PIXELS = 6;
const GLYPH_HEIGHT_PIXELS = 8;
const NUM_GLYPHS = 256;
const BYTES_PER_GLYPH = GLYPH_HEIGHT_PIXELS;
const EXPECTED_FILE_SIZE = NUM_GLYPHS * BYTES_PER_GLYPH; // 2048 bytes

// SVG pixel size (purely visual)
const SVG_PIXEL_SIZE = 10;
const SVG_WIDTH = GLYPH_WIDTH_PIXELS * SVG_PIXEL_SIZE;
const SVG_HEIGHT = GLYPH_HEIGHT_PIXELS * SVG_PIXEL_SIZE;

// Sprite sheet layout
const SPRITE_COLS = 16;
const SPRITE_ROWS = Math.ceil(NUM_GLYPHS / SPRITE_COLS);

// Font metrics (TrueType units)
const FONT_EM = 1000;
const FONT_PIXEL_SIZE = 100; // 1 bitmap pixel -> 100 font units
const FONT_ASCENT = GLYPH_HEIGHT_PIXELS * FONT_PIXEL_SIZE; // 8*100 = 800
const FONT_DESCENT = FONT_EM - FONT_ASCENT; // 200
const GLYPH_ADVANCE = GLYPH_WIDTH_PIXELS * FONT_PIXEL_SIZE; // 6*100 = 600

const SVG_BACKGROUND_COLOR = "black";
const SVG_PIXEL_COLOR = "lightgreen";

function readBitmap(p: string): Uint8Array {
    const data = fs.readFileSync(p);
    if (data.length !== EXPECTED_FILE_SIZE) {
        throw new Error(
            `Expected file size ${EXPECTED_FILE_SIZE} bytes (256 glyphs × 8 bytes), got ${data.length} bytes.`
        );
    }
    return data;
}

/**
 * Extract 8x6 bitmap for glyph_index.
 * bits[row][col] in {0,1}.
 */
function extractGlyphBits(data: Uint8Array, glyphIndex: number): number[][] {
    const start = glyphIndex * BYTES_PER_GLYPH;
    const rows = data.subarray(start, start + BYTES_PER_GLYPH);

    const bits: number[][] = [];
    for (const rowByte of rows) {
        const rowBits: number[] = [];
        for (let col = 0; col < GLYPH_WIDTH_PIXELS; col++) {
            const bitIndex = 5 - col;
            const value = ((rowByte ^ 0xff) >> bitIndex) & 0x01;
            rowBits.push(value);
        }
        bits.push(rowBits);
    }
    return bits;
}

function glyphToSVG(glyphBits: number[][]): string {
    const parts: string[] = [];
    parts.push('<?xml version="1.0" encoding="UTF-8"?>');
    parts.push(
        `<svg xmlns="http://www.w3.org/2000/svg" ` +
            `shape-rendering="crispEdges" ` +
            `width="${SVG_WIDTH}" height="${SVG_HEIGHT}" ` +
            `viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}">`
    );
    parts.push(`  <rect x="0" y="0" width="100%" height="100%" fill="${SVG_BACKGROUND_COLOR}" />`);

    for (let row = 0; row < GLYPH_HEIGHT_PIXELS; row++) {
        for (let col = 0; col < GLYPH_WIDTH_PIXELS; col++) {
            if (glyphBits[row][col]) {
                const x = col * SVG_PIXEL_SIZE;
                const y = row * SVG_PIXEL_SIZE;
                parts.push(
                    `  <rect x="${x}" y="${y}" width="${SVG_PIXEL_SIZE}" height="${SVG_PIXEL_SIZE}" fill="${SVG_PIXEL_COLOR}" />`
                );
            }
        }
    }

    parts.push("</svg>");
    return parts.join("\n");
}

function spriteSheetSVG(allGlyphBits: number[][][]): string {
    const sheetWidth = SPRITE_COLS * SVG_WIDTH;
    const sheetHeight = SPRITE_ROWS * SVG_HEIGHT;

    const parts: string[] = [];
    parts.push('<?xml version="1.0" encoding="UTF-8"?>');
    parts.push(
        `<svg xmlns="http://www.w3.org/2000/svg" ` +
            `width="${sheetWidth}" height="${sheetHeight}" ` +
            `viewBox="0 0 ${sheetWidth} ${sheetHeight}">`
    );
    parts.push(`  <rect x="0" y="0" width="100%" height="100%" fill="${SVG_BACKGROUND_COLOR}" />`);

    for (let glyphIndex = 0; glyphIndex < allGlyphBits.length; glyphIndex++) {
        const glyphBits = allGlyphBits[glyphIndex];
        const gx = (glyphIndex % SPRITE_COLS) * SVG_WIDTH;
        const gy = Math.floor(glyphIndex / SPRITE_COLS) * SVG_HEIGHT;

        parts.push(`  <g transform="translate(${gx},${gy})">`);

        for (let row = 0; row < GLYPH_HEIGHT_PIXELS; row++) {
            for (let col = 0; col < GLYPH_WIDTH_PIXELS; col++) {
                if (glyphBits[row][col]) {
                    const x = col * SVG_PIXEL_SIZE;
                    const y = row * SVG_PIXEL_SIZE;
                    parts.push(
                        `    <rect x="${x}" y="${y}" width="${SVG_PIXEL_SIZE}" height="${SVG_PIXEL_SIZE}" fill="${SVG_PIXEL_COLOR}" />`
                    );
                }
            }
        }

        parts.push("  </g>");
    }

    parts.push("</svg>");
    return parts.join("\n");
}

function buildTTF(allGlyphBits: number[][][], ttfPath: string): void {
    const glyphs: opentype.Glyph[] = [];

    // .notdef glyph (index 0) – NO unicode
    const notdef = new opentype.Glyph({
        name: ".notdef",
        advanceWidth: GLYPH_ADVANCE,
        path: new opentype.Path(),
    });
    glyphs.push(notdef);

    // Choose an offset so glyph 0 maps to U+0100, glyph 1 to U+0101, etc.
    const UNICODE_OFFSET = 0x0100;

    // Glyphs 1..256: g00..gff
    for (let code = 0; code < NUM_GLYPHS; code++) {
        const name = `g${code.toString(16).toUpperCase().padStart(2, "0")}`;
        const bits = allGlyphBits[code];

        const path = new (opentype as any).Path();

        let firstCol = GLYPH_WIDTH_PIXELS;
        let anyOn = false;

        for (let row = 0; row < GLYPH_HEIGHT_PIXELS; row++) {
            for (let col = 0; col < GLYPH_WIDTH_PIXELS; col++) {
                if (!bits[row][col]) continue;

                anyOn = true;
                if (col < firstCol) firstCol = col;

                const x0 = col * FONT_PIXEL_SIZE;
                const x1 = (col + 1) * FONT_PIXEL_SIZE;

                // row 0 = top -> highest y
                const yBottom = (GLYPH_HEIGHT_PIXELS - 1 - row) * FONT_PIXEL_SIZE;
                const yTop = yBottom + FONT_PIXEL_SIZE;

                path.moveTo(x0, yBottom);
                path.lineTo(x1, yBottom);
                path.lineTo(x1, yTop);
                path.lineTo(x0, yTop);
                path.closePath();
            }
        }

        const lsb = anyOn ? firstCol * FONT_PIXEL_SIZE : 0;

        const glyph = new opentype.Glyph({
            name,
            unicode: UNICODE_OFFSET + code, // U+0100..U+01FF
            advanceWidth: GLYPH_ADVANCE,
            leftSideBearing: lsb,
            path,
        });

        glyphs.push(glyph);
    }

    const font = new opentype.Font({
        familyName: "Radio86RKPixel",
        styleName: "Regular",
        unitsPerEm: FONT_EM,
        ascender: FONT_ASCENT,
        descender: -FONT_DESCENT,
        glyphs,
    });

    const arrayBuffer: ArrayBuffer = font.toArrayBuffer();
    const buf = Buffer.from(arrayBuffer);
    fs.writeFileSync(ttfPath, buf);
}

function main(bitmapPath: string, svgDir: string, ttfPath: string): void {
    const data = readBitmap(bitmapPath);

    const outDir = svgDir;
    fs.mkdirSync(outDir, { recursive: true });

    const allGlyphBits: number[][][] = [];

    for (let glyphIndex = 0; glyphIndex < NUM_GLYPHS; glyphIndex++) {
        const bits = extractGlyphBits(data, glyphIndex);
        allGlyphBits.push(bits);

        const svgText = glyphToSVG(bits);
        const filename = `glyph_${glyphIndex.toString(16).padStart(2, "0")}.svg`;
        fs.writeFileSync(path.join(outDir, filename), svgText, { encoding: "utf-8" });
    }

    const sprite = spriteSheetSVG(allGlyphBits);
    fs.writeFileSync(path.join(outDir, "sprite.svg"), sprite, { encoding: "utf-8" });

    buildTTF(allGlyphBits, ttfPath);

    console.log(`Generated ${NUM_GLYPHS} SVGs in ${outDir}`);
    console.log(`Generated sprite: ${path.join(outDir, "sprite.svg")}`);
    console.log(`Generated TTF: ${ttfPath}`);
}

if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length !== 3) {
        console.error(`usage: ${path.basename(process.argv[1])} <font_bitmap.bin> <output_svg_dir> <output_font.ttf>`);
        process.exit(1);
    }
    const [bitmapPath, svgDir, ttfPath] = args;
    main(bitmapPath, svgDir, ttfPath);
}
