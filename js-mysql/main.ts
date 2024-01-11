import mysql from "npm:mysql2";
import process from "npm:process";

import { parseArgs } from "https://deno.land/std@0.211.0/cli/parse_args.ts";

const args = parseArgs(Deno.args);

const env = process.env;
const db_url = env.MYSQL_URL;
console.assert(db_url, "MYSQL_URL is not set");

export type User = {
    ID: number;
    user_login: string;
    user_pass?: string;
    user_nicename: string;
    user_email: string;
    user_url: string;
    user_registered: string;
    user_activation_key?: string;
    user_status: number;
    display_name: string;
    purchased?: boolean;
};

const user_login = args.user;
console.log({ user_login });

const connection = mysql.createConnection(db_url!);
try {
    connection.ping();
    const sql_ = `
        SELECT *
            FROM wp_users u, wp_usermeta m
        WHERE
            u.ID = m.user_id and
            m.meta_key = "wp_capabilities"`;
    const byUser = `and u.user_login = ?`;
    const sql = sql_ + (user_login ? byUser : "");
    console.log(sql);
    connection.connect();
    console.log("connected to", db_url);
    const [results, _] = await connection.promise().query(sql, [user_login]);
    console.log(results);
} finally {
    connection.end();
    console.log("disconnected");
}
