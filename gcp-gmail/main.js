import { google } from "googleapis";

const env = process.env;

const oauth2Client = new google.auth.OAuth2(
    env.GOOGLE_OAUTH2_CLIENT_ID,
    env.GOOGLE_OAUTH2_CLIENT_SECRET
);

oauth2Client.setCredentials({ refresh_token: env.GOOGLE_OAUTH2_REFRESH_TOKEN });

const gmail = google.gmail("v1");
const labels = await gmail.users.labels.list({
    auth: oauth2Client,
    userId: "me",
});

console.log(labels.data.labels.map((label) => label.name).join("\n"));
