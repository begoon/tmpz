import * as fs from "node:fs";
import * as path from "node:path";

function createPDF(path: string) {
    const parts: string[] = [];
    const offsets: number[] = [];
    let position = 0;

    function append(str: string) {
        parts.push(str);
        position += Buffer.byteLength(str, "utf8");
    }

    // 1. Header
    append("%PDF-1.4\n");
    offsets[0] = 0; // free object

    // ------------------------------------------------------------
    // Content stream: text + rectangle + SVG-like triangle
    // ------------------------------------------------------------

    const contentLines: string[] = [];

    // Text with built-in Helvetica
    contentLines.push(
        "BT",
        "/F1 24 Tf", // built-in Helvetica
        "72 750 Td", // position near top-left
        "(Hello with Helvetica!) Tj",
        "ET",
        ""
    );

    // Draw a stroked rectangle: x=100, y=600, width=200, height=50
    contentLines.push(
        "2 w", // line width
        "0 0 1 RG", // stroke color = blue (RGB)
        "100 600 200 50 re", // rectangle
        "S",
        ""
    );

    // Simple SVG-like triangle: M 100 400 L 200 500 L 300 400 Z
    contentLines.push(
        "0.5 0.5 0.5 rg", // fill color gray
        "100 400 m",
        "200 500 l",
        "300 400 l",
        "h", // close path
        "f", // fill
        ""
    );

    const contentStreamBody = contentLines.join("\n") + "\n";
    const contentLength = Buffer.byteLength(contentStreamBody, "utf8");

    // ------------------------------------------------------------
    // Objects:
    // 1: Catalog
    // 2: Pages
    // 3: Page
    // 4: Content stream
    // 5: Font (built-in Helvetica)
    // ------------------------------------------------------------

    const obj1 = "1 0 obj\n" + "<< /Type /Catalog\n" + "   /Pages 2 0 R\n" + ">>\n" + "endobj\n";

    const obj2 = "2 0 obj\n" + "<< /Type /Pages\n" + "   /Kids [3 0 R]\n" + "   /Count 1\n" + ">>\n" + "endobj\n";

    const obj3 =
        "3 0 obj\n" +
        "<< /Type /Page\n" +
        "   /Parent 2 0 R\n" +
        "   /MediaBox [0 0 595 842]\n" + // A4-ish
        "   /Contents 4 0 R\n" +
        "   /Resources << /Font << /F1 5 0 R >> >>\n" +
        ">>\n" +
        "endobj\n";

    const obj4 =
        "4 0 obj\n" + `<< /Length ${contentLength} >>\n` + "stream\n" + contentStreamBody + "endstream\n" + "endobj\n";

    // Built-in Helvetica font: no embedding, no Widths, no FontFile
    const obj5 =
        "5 0 obj\n" +
        "<< /Type /Font\n" +
        "   /Subtype /Type1\n" +
        "   /BaseFont /Helvetica\n" +
        "   /Encoding /WinAnsiEncoding\n" +
        ">>\n" +
        "endobj\n";

    const allObjects = [obj1, obj2, obj3, obj4, obj5];

    // Write objects and record offsets
    for (let i = 0; i < allObjects.length; i++) {
        const id = i + 1;
        offsets[id] = position;
        append(allObjects[i]);
    }

    const xrefOffset = position;
    const objectCount = allObjects.length; // 5

    // xref
    let xref = "xref\n";
    xref += `0 ${objectCount + 1}\n`;
    xref += "0000000000 65535 f \n"; // free object 0

    for (let i = 1; i <= objectCount; i++) {
        const offsetString = offsets[i].toString().padStart(10, "0");
        xref += `${offsetString} 00000 n \n`;
    }

    append(xref);

    // Trailer
    let trailer = "trailer\n";
    trailer += `<< /Size ${objectCount + 1}\n`;
    trailer += "   /Root 1 0 R\n";
    trailer += ">>\n";
    trailer += "startxref\n";
    trailer += `${xrefOffset}\n`;
    trailer += "%%EOF\n";

    append(trailer);

    const pdfContent = parts.join("");
    fs.writeFileSync(path, pdfContent, { encoding: "utf8" });

    console.log(`pdf written to: ${path}`);
}

// --- CLI entrypoint ---

function main() {
    const arg = process.argv[2];
    const output = arg ? path.resolve(process.cwd(), arg) : path.resolve(process.cwd(), "builtin.pdf");

    createPDF(output);
}

if (require.main === module) {
    main();
}
