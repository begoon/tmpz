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

console.time("configuration");
const configuration = Object.fromEntries(
    (
        await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: "configuration",
        })
    ).data.values
);
console.timeEnd("configuration");
configuration.list = JSON.parse(configuration.list);
configuration.dict = JSON.parse(configuration.dict);
configuration.counter = Number(configuration.counter);
configuration.updated_at = new Date(configuration.updated_at);
console.log(configuration);

await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: "configuration!counter",
    valueInputOption: "USER_ENTERED",
    resource: {
        values: [[configuration.counter * 2]],
    },
});
await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId,
    requestBody: {
        valueInputOption: "USER_ENTERED",
        data: [
            {
                range: "configuration!counter",
                values: [[configuration.counter * 2]],
            },
            {
                range: "configuration!updated_at",
                values: [[new Date().toISOString()]],
            },
        ],
    },
});
