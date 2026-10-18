import { describe, expect, test, afterAll } from "bun:test";
import { handle } from "../src/app";
import { db, quote, identifier, relation } from "../src/db";
import { esc } from "../src/ui";
const table = `codex_test_${Date.now()}`;
const auth: Record<string, string> = process.env.ADMIN_PASSWORD
  ? {
      authorization:
        "Basic " +
        Buffer.from(`admin:${process.env.ADMIN_PASSWORD}`).toString("base64"),
    }
  : {};

async function request(path: string, data?: Record<string, string>) {
  return handle(
    new Request("http://localhost:3000" + path, {
      method: data ? "POST" : "GET",
      headers: {
        ...auth,
        ...(data ? { origin: "http://localhost:3000" } : {}),
      },
      body: data ? new URLSearchParams(data) : undefined,
    }),
  );
}

test("HTML and SQL identifier escaping", () => {
  expect(esc('<script>"&')).toBe("&lt;script&gt;&quot;&amp;");
  expect(quote('a"b')).toBe('"a""b"');
  expect(() => identifier("x".repeat(64))).toThrow();
});
test("cross-origin mutations are rejected", async () => {
  const res = await handle(
    new Request("http://localhost:3000/rows/add", {
      method: "POST",
      headers: auth,
    }),
  );
  expect(res.status).toBe(403);
});
test("production requires authentication", async () => {
  const previous = process.env.VERCEL;
  process.env.VERCEL = "1";
  try {
    expect((await handle(new Request("http://localhost:3000/"))).status).toBe(
      401,
    );
  } finally {
    if (previous === undefined) delete process.env.VERCEL;
    else process.env.VERCEL = previous;
  }
});
describe.skipIf(process.env.INTEGRATION !== "1")(
  "real PostgreSQL lifecycle",
  () => {
    afterAll(async () => {
      await db.unsafe(`DROP TABLE IF EXISTS ${relation(table)}`);
      await db.close();
    });
    test("create, insert, browse, stale deletion, SQL, and drop", async () => {
      const form = new FormData();
      form.set("table", table);
      for (const name of ["id", "title", "optional", "enabled"])
        form.append("column", name);
      for (const type of ["bigint", "text", "text", "boolean"])
        form.append("type", type);
      form.set("primary_0", "on");
      form.set("auto_0", "on");
      let res = await handle(
        new Request("http://localhost:3000/tables/create", {
          method: "POST",
          headers: { ...auth, origin: "http://localhost:3000" },
          body: form,
        }),
      );
      expect(await res.text()).toContain("Table created.");
      res = await request("/rows/add", {
        table,
        mode_1: "value",
        value_1: '<script>alert("test")</script>\' Ω',
        mode_2: "null",
        mode_3: "value",
        value_3: "false",
      });
      expect(await res.text()).toContain("Row added.");
      let rows = await db.unsafe(
        `SELECT *,ctid::text tid,xmin::text version,tableoid::text oid FROM ${relation(table)}`,
      );
      expect(rows.length).toBe(1);
      expect(rows[0].enabled).toBe(false);
      expect(rows[0].optional).toBeNull();
      res = await request("/?table=" + table);
      const page = await res.text();
      expect(page).toContain("&lt;script&gt;");
      expect(page).not.toContain("<script>alert");
      const old = rows[0];
      await db.unsafe(`UPDATE ${relation(table)} SET title='updated'`);
      res = await request("/rows/delete", {
        table,
        tid: old.tid,
        version: old.version,
        oid: old.oid,
      });
      expect(await res.text()).toContain("row changed");
      rows = await db.unsafe(
        `SELECT ctid::text tid,xmin::text version,tableoid::text oid FROM ${relation(table)}`,
      );
      res = await request("/rows/delete", { table, ...rows[0] });
      expect(await res.text()).toContain("Row deleted.");
      res = await request("/query", { sql: "SELECT 42 AS answer" });
      expect(await res.text()).toContain("<td>42</td>");
      res = await request("/tables/drop", { table });
      expect(await res.text()).toContain("Table dropped.");
    }, 30000);
  },
);
