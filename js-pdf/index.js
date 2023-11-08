import fs from "fs";
import { LoremIpsum } from "lorem-ipsum";
import pdfmake from "pdfmake";

const lorem = new LoremIpsum({
    sentencesPerParagraph: {
        max: 8,
        min: 4,
    },
    wordsPerSentence: {
        max: 16,
        min: 4,
    },
});

const doc = {
    pageMargins: [10, 10, 10, 10],
    pageOrientation: "landscape",
    watermark: {
        text: "freemynd.io",
        color: "blue",
        opacity: 0.1,
        bold: true,
        italics: false,
    },
    patterns: {
        stripe45d: {
            boundingBox: [1, 1, 4, 4],
            xStep: 3,
            yStep: 3,
            pattern: "1 w 0 1 m 4 5 l s 2 0 m 5 3 l s",
        },
    },
    background: {
        canvas: [
            {
                type: "rect",
                x: 0,
                y: 0,
                w: "1000",
                h: 400,
                color: "lightblue",
                fillOpacity: 0.5,
            },
        ],
    },
    content: [
        {
            text: "Карта твоего характера",
            margins: [0, 0, 0, 8],
            fontSize: 60,
        },
        { qr: lorem.generateWords(16), fit: 100, alignment: "right" },
        "\n",
        {
            text: lorem.generateSentences(5),
            margins: [0, 0, 0, 8],
            fontSize: 20,
        },
        "\n",
        {
            columns: [
                {
                    text: lorem.generateParagraphs(7),
                    alignment: "left",
                },
                {
                    text: lorem.generateParagraphs(7),
                    alignment: "right",
                },
            ],
        },
        "\n",
        {
            canvas: [
                {
                    type: "rect",
                    x: 0,
                    y: 0,
                    w: 600,
                    h: 400,
                    color: "yellow",
                    fillOpacity: 0.5,
                },
            ],
        },
    ],
};

const printer = new pdfmake({
    Roboto: {
        normal: "./fonts/Roboto-Regular.ttf",
        bold: "./fonts/Roboto-Medium.ttf",
        italics: "./fonts/Roboto-Italic.ttf",
        bolditalics: "./fonts/Roboto-MediumItalic.ttf",
    },
});

const pdf = printer.createPdfKitDocument(doc);
pdf.pipe(fs.createWriteStream("doc.pdf"));
pdf.end();
