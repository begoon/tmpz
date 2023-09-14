import { google } from "googleapis";

const env = process.env;

function decodeEntities(encodedString) {
    var translate_re = /&(nbsp|amp|quot|lt|gt);/g;
    var translate = {
        nbsp: " ",
        amp: "&",
        quot: '"',
        lt: "<",
        gt: ">",
    };
    return encodedString
        .replace(translate_re, function (match, entity) {
            return translate[entity];
        })
        .replace(/&#(\d+);/gi, function (match, numStr) {
            var num = parseInt(numStr, 10);
            return String.fromCharCode(num);
        });
}

function hash(str) {
    let hash = 5381;
    let i = str.length;
    while (i--) hash = ((hash << 5) - hash) ^ str.charCodeAt(i);
    return (hash >>> 0).toString(36);
}

const oauth2Client = new google.auth.OAuth2(
    env.GOOGLE_OAUTH2_CLIENT_ID,
    env.GOOGLE_OAUTH2_CLIENT_SECRET
);

oauth2Client.setCredentials({ refresh_token: env.GOOGLE_OAUTH2_REFRESH_TOKEN });

const gmail = google.gmail("v1");

const profile = await gmail.users.getProfile({
    auth: oauth2Client,
    userId: "me",
});
console.log("logged in as", profile.data);

const labels_ = (
    await gmail.users.labels.list({
        auth: oauth2Client,
        userId: "me",
    })
).data.labels
    .map((label) => [label.name, label.id])
    .sort((a, b) => a[0] > b[0]);

const labels = new Map(labels_);
const labelIds = new Map(labels_.map(([name, id]) => [id, name]));

if (process.argv.includes("--labels")) {
    console.log("labels", labels);
    process.exit(0);
}

const label = process.argv[2];
if (!label) {
    console.log("usage: node|bun main.js <label>");
    process.exit(1);
}

const labelID = labels.get(label);
if (!labelID) {
    console.log("label not found", label);
    process.exit(1);
}

const filter = [labelID];
console.log(`filter label "${label}"`, filter.join(""), labelIds.get(labelID));

const options = {
    auth: oauth2Client,
    userId: "me",
    labelIds: filter,
    maxResults: 500,
};

const ids = [];

let n = 0;
let page = 0;
while (true) {
    const response_ = await gmail.users.messages.list(options);
    const response = response_.data;
    n += response.messages?.length || 0;
    ids.push(...(response.messages || []).map((m) => m.id));
    console.log("#", page, response.messages?.length, response.nextPageToken);
    if (process.argv.includes("--messages")) {
        for (const message of response.messages) {
            const msg = await gmail.users.messages.get({
                auth: oauth2Client,
                userId: "me",
                id: message.id,
            });
            console.log(
                Object.fromEntries(
                    Object.entries({
                        ...msg.data,
                        snippet: undefined,
                        historyId: undefined,
                        payload: undefined,
                        raw: undefined,
                        labelIds: msg.data.labelIds
                            .map((id) => labelIds.get(id) || id)
                            .sort()
                            .join(", "),
                        date: new Date(
                            Number(msg.data.internalDate)
                        ).toISOString(),
                    }).filter(([k, v]) => v)
                )
            );
            console.log(decodeEntities(msg.data.snippet));
        }
    }
    if (!response.nextPageToken) break;
    options.pageToken = response.nextPageToken;
    page += 1;
}
console.log("n", n, ids.length);
if (!n) {
    console.log("no messages found");
    process.exit(0);
}

if (process.argv.includes("--mark")) {
    const DELETED_LABEL = "DELETEDx";
    const DELETED_LABEL_ID = labels.get(DELETED_LABEL);

    if (!DELETED_LABEL_ID) {
        console.log("creating label", DELETED_LABEL);
        const createdLabelRequest = {
            name: DELETED_LABEL,
            messageListVisibility: "show",
            labelListVisibility: "labelShow",
            type: "user",
        };
        console.log("createdLabelRequest", createdLabelRequest.data);
        const created = await gmail.users.labels.create({
            auth: oauth2Client,
            userId: "me",
            requestBody: createdLabelRequest,
        });
        console.log("created", created);
        process.exit(0);
    }

    console.log(`mark ${n} messages with ${DELETED_LABEL}/${DELETED_LABEL_ID}`);

    const modified = await gmail.users.messages.batchModify({
        auth: oauth2Client,
        userId: "me",
        requestBody: { ids, addLabelIds: [DELETED_LABEL_ID] },
    });
    console.log("modified", modified.status);
}

if (process.argv.includes("--delete")) {
    console.log("deleting", ids.length, "messages");
    const deleted = await gmail.users.messages.batchDelete({
        auth: oauth2Client,
        userId: "me",
        requestBody: { ids },
    });
    console.log("deleted", deleted.status);
}
