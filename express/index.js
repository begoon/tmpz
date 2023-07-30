const express = require("express");
const app = express();
const port = 3000;
const serveIndex = require("serve-index");

app.use(
    "/fs",
    express.static("/", { dotfiles: "allow" }),
    serveIndex("/", { icons: true, hidden: true, view: "details" })
);

app.listen(port, () => {
    console.log(`Example app listening on port ${port}`);
});
