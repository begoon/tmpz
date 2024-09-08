import { Database } from "https://deno.land/x/sqlite3@0.12.0/mod.ts";

const db = new Database("test.db");

db.close();
