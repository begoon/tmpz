import { createClient } from "@libsql/client/web";

import dotenv from "dotenv";
dotenv.config();

const client = createClient({
    url: "libsql://first-begoon.turso.io",
    authToken: process.env.TURSO_AUTH_TOKEN,
});

try {
    const rs = await client.execute("select * from sessions");
    console.log(rs);
} catch (e) {
    console.error(e);
}
