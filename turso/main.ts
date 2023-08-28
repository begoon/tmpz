import { createClient } from "@libsql/client/web";
import { load } from "https://deno.land/std@0.197.0/dotenv/mod.ts";

await load({ export: true });

const token = Deno.env.get("TURSO_AUTH_TOKEN");
const user_id = Deno.env.get("USER_ID") || "*";

console.time("createClient");
const client = createClient({
    url: "libsql://first-begoon.turso.io",
    authToken: token,
});
console.timeEnd("createClient");

import { db } from "./db.ts";

const cmd = Deno.args[0];

try {
    const rs = await client.execute("select * from sessions");
    console.log(rs);
    if (rs.rows.length) {
        const row = rs.rows[0];
        console.log(row.user_id);
        console.log(JSON.parse(row.session as string));
    }
    if (cmd === "create") {
        console.time("execute");
        const rs = await client.execute({
            sql: "insert into sessions values (:user_id, :sessions)",
            args: {
                user_id,
                sessions: JSON.stringify(db, null, 2),
            },
        });
        console.timeEnd("execute");
    }
} catch (e) {
    console.error(e);
}
