import dotenv from "dotenv";
import fs from "fs";
import { Client } from "ssh2";

dotenv.config();
const env = process.env;

const path = env.FREEMYND_SFTP_STORAGE_DIR + "/dashok";
const filename = process.argv[2];
const content = fs.readFileSync(filename);

console.log(filename, content.length);

console.time("sftp");

const conn = new Client();

console.timeLog("sftp", "client");

let first = true;

conn.connect({
    host: env.FREEMYND_SFTP_HOST,
    username: env.FREEMYND_SFTP_USER,
    port: env.FREEMYND_SFTP_PORT,
    privateKey: Buffer.from(env.FREEMYND_SFTP_KEY, "base64").toString(),
    passphrase: env.FREEMYND_SFTP_PASS,
    debug: (msg) => {
        // console.debug(msg);
    },
})
    .on("ready", () => {
        console.timeLog("sftp", "ready");
        conn.sftp((error, sftp) => {
            if (error) throw error;
            console.time("fastPut");
            sftp.fastPut(
                filename,
                path + "/" + filename,
                {
                    step: (total, nb, fsize) => {
                        if (first) {
                            console.timeLog("sftp", "first");
                            first = false;
                        }
                        const percent = Math.round((total / fsize) * 100);
                        const status = `${percent}% ${total} ${fsize} ${nb}`;
                        // console.log(status);
                        process.stdout.write("\r" + status);
                    },
                },
                (error) => {
                    if (error) throw error;
                    conn.end();
                    console.log("");
                    console.timeEnd("fastPut");
                    console.timeLog("sftp", "saved");
                }
            );
        });
    })
    .on("close", () => console.timeLog("sftp", "close"))
    .on("error", (err) => {
        throw new Error(err);
    })
    .on("end", () => console.timeLog("sftp", "end"))
    .on("handshake", (handshake) => console.timeLog("sftp", "handshake"));
