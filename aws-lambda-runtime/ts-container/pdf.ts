import type { WriteStream } from "node:fs";

import blobStream from "npm:blob-stream";
import PDFDocument from "npm:pdfkit";

export async function pdf() {
    const stream = blobStream();
    create(stream as unknown as WriteStream);

    const { promise, resolve } = Promise.withResolvers<Blob>();
    stream.on("finish", () => resolve(stream.toBlob()));

    const content = await promise;
    console.log(content);
    return content;
}

export function create(stream: WriteStream) {
    const doc = new PDFDocument();

    doc.pipe(stream);

    doc.fontSize(25).text("Some text with an embedded font!", 100, 100);

    doc.addPage()
        .fontSize(25)
        .text("Here is some vector graphics...", 100, 100);

    doc.save()
        .moveTo(100, 150)
        .lineTo(100, 250)
        .lineTo(200, 250)
        .fill("#FF3300");

    doc.scale(0.6)
        .translate(470, -380)
        .path("M 250,75 L 323,301 131,161 369,161 177,301 z")
        .fill("red", "even-odd")
        .restore();

    doc.addPage()
        .fillColor("blue")
        .text("Here is a link!", 100, 100)
        .underline(100, 100, 160, 27, { color: "#0000FF" })
        .link(100, 100, 160, 27, "http://google.com/");

    doc.end();
}
