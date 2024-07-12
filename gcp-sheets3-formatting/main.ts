import { google } from "googleapis";
import { env } from "node:process";
import { L } from "./L.ts";

if (!env.GCLOUD_CREDENTIALS) throw new Error("GCLOUD_CREDENTIALS not set");

const oauth2Client = new google.auth.GoogleAuth({
    keyFile: env.GCLOUD_CREDENTIALS,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth: oauth2Client });

const spreadsheet = env.SPREADSHEET_ID;
if (!spreadsheet) throw new Error("SPREADSHEET_ID not set");

console.log({ spreadsheet });

const BLACK = { red: 0, green: 0, blue: 0 };
const WHITE = { red: 1, green: 1, blue: 1 };
const YELLOW = { red: 1, green: 1, blue: 0 };

type Cell = { text: string; bold?: boolean };

async function insert(spreadsheet: string, rows: Cell[][]) {
    const requests = rows.map((row, r) => ({
        // appendCells: {
        updateCells: {
            range: { sheetId: 0, startRowIndex: r, endRowIndex: r + 1 },
            rows: [
                {
                    values: row.map((cell, c) => ({
                        userEnteredValue: {
                            stringValue: cell.text?.replace("\n", "\n\n"),
                        },
                        userEnteredFormat: {
                            textFormat: {
                                bold: c == 0 ? cell.bold : false,
                                foregroundColor: BLACK,
                            },
                            backgroundColor: c ? WHITE : YELLOW,
                            wrapStrategy: "WRAP",
                            verticalAlignment: "TOP",
                        },
                    })),
                },
            ],
            fields: [
                "userEnteredValue.stringValue",
                "userEnteredFormat.textFormat",
                "userEnteredFormat.backgroundColor",
                "userEnteredFormat.wrapStrategy",
                "userEnteredFormat.verticalAlignment",
            ].join(","),
        },
    }));

    await sheets.spreadsheets.batchUpdate({
        spreadsheetId: spreadsheet,
        resource: { requests },
    });
}

const rows = Object.entries(L).map(([id, { ru, ua, tag }]) => [
    { text: id },
    { text: ru },
    { text: ua },
    { text: tag },
]);

console.log({ rows });

await insert(spreadsheet, rows);
await columnsWidth(spreadsheet!, 0);

// --------------

async function columnsWidth(spreadsheetId: string, col: number) {
    const request = {
        spreadsheetId,
        resource: {
            requests: [
                {
                    updateDimensionProperties: {
                        range: {
                            sheetId: 0,
                            dimension: "COLUMNS",
                            startIndex: col,
                            endIndex: col + 3,
                        },
                        properties: {
                            pixelSize: 400,
                        },
                        fields: "pixelSize",
                    },
                },
            ],
        },
    };

    const response = await sheets.spreadsheets.batchUpdate(request);
    console.log(response["statusText"]);
}
