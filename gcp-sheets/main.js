import { google } from "googleapis";

const oauth2Client = new google.auth.GoogleAuth({
    keyFile: "credentials.json",
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});

const sheets = google.sheets({ version: "v4", auth: oauth2Client });

const spreadsheetId = process.env.SPREADSHEET_ID;

const appendOptions = {
    spreadsheetId,
    range: "data",
    valueInputOption: "USER_ENTERED",
    resource: {
        values: [["=now()", "this", "was", "inserted", "via", "node.js"]],
    },
};

sheets.spreadsheets.values.append(appendOptions);

console.log(
    JSON.stringify(await sheets.spreadsheets.get({ spreadsheetId }), null, 2)
);

console.log(
    (await sheets.spreadsheets.values.get({ spreadsheetId, range: "data" }))
        .data
);
