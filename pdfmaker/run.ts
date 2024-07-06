import fs from "node:fs";
import { PDFDocument as PDFLibDocument } from "npm:pdf-lib";
import PDFDocument from "npm:pdfkit";

export async function create() {
    const doc = new PDFDocument();

    doc.pipe(fs.createWriteStream("output-generated.pdf"));

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

    const originalPDF_ = fs.readFileSync("output-generated.pdf");
    const donorPDF_ = fs.readFileSync("output-donor.pdf");

    const originalPDF = await PDFLibDocument.load(originalPDF_);
    const donorPDF = await PDFLibDocument.load(donorPDF_);

    const merged = await PDFLibDocument.create();

    const [originals] = await merged.copyPages(originalPDF, [1, 1]);
    const [donated] = await merged.copyPages(donorPDF, [1, 8]);

    merged.addPage(originals);
    merged.insertPage(0, donated);

    fs.writeFileSync("output-merged.pdf", await merged.save());
}
