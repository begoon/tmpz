import { google } from "googleapis";
import { env } from "process";

const SHEET_ID = env.SHEET_ID;
console.log({ SHEET_ID });

const auth = await google.auth.getClient({
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const api = google.sheets({ version: "v4", auth });
const response = await api.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: "Main!A:C",
});

const sz = response.data.values?.length ?? 0;
console.log({ sz });
for (let row of response.data.values!) {
    console.log(row.join(", "));
}

const values = [
    [new Date().toISOString(), "added", "now"],
    ["=LEN(A1)", "B", "C"],
    ["D", "E", "£100.00"],
    ["G", "H", "I"],
];

await api.spreadsheets.values.update({
    spreadsheetId: SHEET_ID,
    range: `Main!A${sz + 1}:C${sz + values.length}`,
    valueInputOption: "USER_ENTERED",
    requestBody: { values },
});
