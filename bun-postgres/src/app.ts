import { timingSafeEqual, createHash } from "node:crypto";
import { db, createTable, insertRow, deleteRow, relation } from "./db";
import { workspace, document, columnEditor, queryResult, esc } from "./ui";
import { css, js, htmx } from "./assets";
const headers = {
  "Content-Type": "text/html; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
};

function authorized(req: Request) {
  const password = process.env.ADMIN_PASSWORD;
  if (!password) return !process.env.VERCEL;
  try {
    const value = req.headers.get("authorization") || "";
    if (!value.startsWith("Basic ")) return false;
    const supplied = Buffer.from(value.slice(6), "base64").toString();
    return timingSafeEqual(
      createHash("sha256").update(supplied).digest(),
      createHash("sha256").update(`admin:${password}`).digest(),
    );
  } catch {
    return false;
  }
}

export async function handle(req: Request): Promise<Response> {
  if (!authorized(req))
    return new Response("Authentication required.", {
      status: 401,
      headers: {
        ...headers,
        "WWW-Authenticate": 'Basic realm="Postgres workspace", charset="UTF-8"',
      },
    });
  const url = new URL(req.url),
    hx = req.headers.get("HX-Request") === "true";

  const html = (body: string, status = 200) =>
    new Response(body, { status, headers });

  if (req.method === "GET") {
    const assets: Record<string, [string, string]> = {
      "/style.css": [css, "text/css"],
      "/app.js": [js, "text/javascript"],
      "/vendor/htmx.min.js": [htmx, "text/javascript"],
    };
    if (assets[url.pathname]) {
      const [body, type] = assets[url.pathname];
      return new Response(body, {
        headers: { ...headers, "Content-Type": type },
      });
    }
    if (url.pathname === "/columns") {
      const i = Number(url.searchParams.get("index"));
      return Number.isInteger(i) && i >= 1 && i < 50
        ? html(columnEditor(i))
        : html("Maximum 50 columns.", 400);
    }
  }
  if (!["GET", "POST"].includes(req.method))
    return html("Method not allowed", 405);
  if (
    req.method === "POST" &&
    (req.headers.get("origin") !== url.origin ||
      req.headers.get("sec-fetch-site") === "cross-site")
  )
    return html("Invalid request origin.", 403);
  let options: Parameters<typeof workspace>[0] = {
    table: url.searchParams.get("table") || undefined,
    view: url.searchParams.get("view") || undefined,
    offset: Math.max(
      0,
      Math.min(
        1000000,
        Number.parseInt(url.searchParams.get("offset") || "0") || 0,
      ),
    ),
  };
  try {
    if (req.method === "POST") {
      const form = await req.formData();
      const table = String(form.get("table") || "");
      options = { table };
      switch (url.pathname) {
        case "/tables/create":
          options.view = "new";
          await createTable(form);
          options = { table, notice: "Table created." };
          break;
        case "/tables/drop":
          await db.unsafe(`DROP TABLE ${relation(table)}`);
          options = { notice: "Table dropped." };
          break;
        case "/rows/add":
          await insertRow(table, form);
          options.notice = "Row added.";
          break;
        case "/rows/delete":
          await deleteRow(table, form);
          options.notice = "Row deleted.";
          break;
        case "/query": {
          const sql = String(form.get("sql") || "").trim();
          options = { view: "sql", sql };
          if (!sql || sql.length > 100000)
            throw new Error(
              "Enter a SQL statement of up to 100,000 characters.",
            );
          const start = performance.now();
          const rows = await db.begin(async (tx) => {
            await tx.unsafe("SET LOCAL statement_timeout = '10s'");
            return await tx.unsafe(sql);
          });
          options.result = queryResult(
            rows,
            rows.count ?? rows.length,
            Math.round(performance.now() - start),
          );
          break;
        }
        default:
          return html("Not found", 404);
      }
    } else if (url.pathname !== "/") return html("Not found", 404);
    const body = await workspace(options);
    return html(hx ? body : document(body));
  } catch (e) {
    const message = (e as Error).message || "Database operation failed.";
    try {
      const body = await workspace({ ...options, error: message });
      return html(hx ? body : document(body));
    } catch {
      return html(
        hx
          ? `<main><div class="alert error">Cannot connect to PostgreSQL. Check the server connection settings.</div></main>`
          : document(
              '<main><div class="alert error">Cannot connect to PostgreSQL. Check the server connection settings.</div></main>',
            ),
        503,
      );
    }
  }
}
