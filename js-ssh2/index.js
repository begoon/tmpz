import dotenv from "dotenv";
import fs from "fs";

import { upload } from "./ssh.js";

dotenv.config();
const env = process.env;

const path = env.FREEMYND_SFTP_STORAGE_DIR + "/dashok";
const filename = process.argv[2];
const content = fs.readFileSync(filename);

console.log(filename, content.length);

upload(
    content,
    path + "/" + filename,
    {
        host: env.FREEMYND_SFTP_HOST,
        username: env.FREEMYND_SFTP_USER,
        port: env.FREEMYND_SFTP_PORT,
        privateKey: Buffer.from(env.FREEMYND_SFTP_KEY, "base64").toString(),
        passphrase: env.FREEMYND_SFTP_PASS,
        debug: (msg) => false && console.debug(msg),
    },
    () => {
        console.log("done");
    }
);
