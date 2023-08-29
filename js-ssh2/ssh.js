import fs from "fs";
import crypto from "node:crypto";
import { Client } from "ssh2";

function tmpfile() {
    return "/tmp/abc-" + crypto.randomBytes(4).readUInt32LE(0) + ".tmp";
}

export function upload(content, path, options, done) {
    const trace = false;
    const cli = false;

    if (trace) console.time("sftp");

    const conn = new Client();

    if (trace) console.timeLog("sftp", "client");

    let first = true;
    conn.connect(options)
        .on("ready", () => {
            if (trace) console.timeLog("sftp", "ready");
            conn.sftp((error, sftp) => {
                if (error) throw error;
                if (trace) console.time("fastPut");

                const tmp = tmpfile();
                console.debug("temp file created", tmp);
                fs.writeFileSync(tmp, content);

                sftp.fastPut(
                    tmp,
                    path,
                    {
                        step: (total, nb, fsize) => {
                            if (first) {
                                if (trace) console.timeLog("sftp", "first");
                                first = false;
                            }
                            const percent = Math.round((total / fsize) * 100);
                            const status = `${percent}% ${total} ${fsize} ${nb}`;
                            if (trace) console.log(status);
                            if (cli) process.stdout.write("\r" + status);
                        },
                    },
                    (error) => {
                        if (error) throw error;
                        conn.end();
                        if (cli) console.log("");
                        if (trace) console.timeEnd("fastPut");
                        if (trace) console.timeLog("sftp", "saved");
                        fs.unlinkSync(tmp);
                        console.debug("temp file removed", tmp);
                        done();
                    }
                );
            });
        })
        .on("close", () => trace && console.timeLog("sftp", "close"))
        .on("error", (error) => {
            throw new Error(error);
        })
        .on("end", () => trace && console.timeLog("sftp", "end"))
        .on("handshake", () => trace && console.timeLog("sftp", "handshake"));
}
