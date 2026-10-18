import { columns, db, quote, relation, tables, types, type Column } from "./db";

export const esc = (v: unknown): string =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );

export const path = (table: string) => "/?table=" + encodeURIComponent(table);

export const hidden = (name: string, value: unknown) =>
  `<input type="hidden" name="${esc(name)}" value="${esc(value)}">`;

export function cell(value: unknown) {
  return value === null
    ? '<span class="null">NULL</span>'
    : esc(typeof value === "object" ? JSON.stringify(value) : value);
}

export function columnEditor(i: number) {
  return `<div class="column-edit"><label>Column name<input name="column" required placeholder="${i ? "name" : "id"}" value="${i ? "" : "id"}"></label><label>Type<select name="type">${types.map((t) => `<option ${t === (i ? "text" : "bigint") ? "selected" : ""}>${t}</option>`).join("")}</select></label><label class="check"><input type="checkbox" name="primary_${i}" ${i ? "" : "checked"}> Primary key</label><label class="check"><input type="checkbox" name="required_${i}"> Required</label><label class="check"><input type="checkbox" name="auto_${i}" ${i ? "" : "checked"}> Auto increment</label></div>`;
}

const newTable = () =>
  `<div class="page-title"><div><p class="eyebrow">SCHEMA DESIGN</p><h1>Create a table</h1><p>Give your data a home. Define its columns and types.</p></div></div><form hx-post="/tables/create" hx-target="#app" class="panel form-panel"><label class="table-name">Table name<input name="table" placeholder="e.g. customers" required maxlength="63"></label><h3>Columns</h3><div id="columns">${columnEditor(0)}</div><button type="button" id="add-column" class="secondary">＋ Add column</button><div class="form-footer"><span class="muted">Schema: public</span><button>Create table</button></div></form>`;

const queryPanel = (sql = "", result = "") =>
  `<div class="page-title"><div><p class="eyebrow">WORKSPACE</p><h1>SQL editor</h1><p>Run SQL directly against your connected database.</p></div></div><form hx-post="/query" hx-target="#app" class="panel"><div class="panel-heading"><span>Query</span><span class="muted">PostgreSQL</span></div><textarea name="sql" class="sql-editor" spellcheck="false" required aria-label="SQL query" placeholder="SELECT * FROM public.your_table LIMIT 100;">${esc(sql)}</textarea><div class="form-footer"><span class="muted">One statement · 10-second timeout · Ctrl / ⌘ + Enter</span><button>Run query →</button></div></form>${result}`;

function rowForm(table: string, cols: Column[]) {
  return `<details class="panel add-row"><summary>＋ Add a row</summary><form hx-post="/rows/add" hx-target="#app">${hidden("table", table)}<div class="fields">${cols
    .filter((c) => !c.generated && c.identity !== "a")
    .map((c) => {
      const i = cols.indexOf(c);
      return `<div class="field"><label for="value-${i}">${esc(c.name)} <small>${esc(c.type)}</small></label><div class="field-input"><select name="mode_${i}" aria-label="${esc(c.name)} value mode"><option value="default">Default / omitted</option><option value="value">Value</option>${c.nullable ? '<option value="null">NULL</option>' : ""}</select><input id="value-${i}" name="value_${i}" placeholder="Enter value" disabled></div></div>`;
    })
    .join(
      "",
    )}</div><div class="form-footer"><span class="muted">Choose Value to enter text, including an empty string.</span><button>Insert row</button></div></form></details>`;
}

async function tablePanel(table: string, offset: number) {
  const cols = await columns(table);
  const rows = await db.unsafe(
    `SELECT json_build_array(${cols.map((c) => quote(c.name) + "::text").join(",")}) AS cells, ctid::text AS tid, xmin::text AS version, tableoid::text AS oid FROM ${relation(table)} ORDER BY tableoid, ctid LIMIT 51 OFFSET $1`,
    [offset],
  );
  const more = rows.length > 50;
  const shown = rows.slice(0, 50);
  return `<div class="page-title"><div><p class="eyebrow">PUBLIC / TABLE</p><h1>${esc(table)}</h1><p>${cols.length} columns <span class="dot">·</span> ${shown.length ? `Rows ${offset + 1}–${offset + shown.length}` : "No rows"}</p></div><form hx-post="/tables/drop" hx-target="#app" hx-confirm="${esc(`Permanently drop public.${table} and all its rows?`)}">${hidden("table", table)}<button class="danger secondary">Drop table</button></form></div>${rowForm(table, cols)}<section class="panel"><div class="panel-heading"><span>Table data</span><a href="${esc(path(table))}" hx-get="${esc(path(table) + "&offset=" + offset)}" hx-target="#app">↻ Refresh</a></div><div class="table-scroll"><table><thead><tr>${cols.map((c) => `<th>${c.primary_key ? '<span title="Primary key">⚿</span> ' : ""}${esc(c.name)}<small>${esc(c.type)}${c.nullable ? "" : " · required"}</small></th>`).join("")}<th class="row-action">Actions</th></tr></thead><tbody>${shown.map((r: { cells: (string | null)[]; tid: string; version: string; oid: string }) => `<tr>${r.cells.map((v: unknown) => `<td>${cell(v)}</td>`).join("")}<td><form hx-post="/rows/delete" hx-target="#app" hx-confirm="Delete this row?">${hidden("table", table)}${hidden("tid", r.tid)}${hidden("version", r.version)}${hidden("oid", r.oid)}<button class="delete-row" aria-label="Delete row">Delete</button></form></td></tr>`).join("") || `<tr><td colspan="${cols.length + 1}"><div class="empty"><strong>This table is empty</strong><p>Add your first row using the form above.</p></div></td></tr>`}</tbody></table></div><div class="pagination"><span>50 rows per page</span><div>${offset > 0 ? `<a hx-get="${esc(path(table) + "&offset=" + Math.max(0, offset - 50))}" hx-target="#app" href="${esc(path(table) + "&offset=" + Math.max(0, offset - 50))}">← Previous</a>` : ""}${more ? `<a hx-get="${esc(path(table) + "&offset=" + (offset + 50))}" hx-target="#app" href="${esc(path(table) + "&offset=" + (offset + 50))}">Next →</a>` : ""}</div></div></section>`;
}

export async function workspace(
  options: {
    table?: string;
    view?: string;
    offset?: number;
    notice?: string;
    error?: string;
    sql?: string;
    result?: string;
  } = {},
) {
  const all = await tables();
  const table = options.table || (!options.view ? all[0]?.name : undefined);
  let content: string;
  try {
    content =
      options.view === "new"
        ? newTable()
        : options.view === "sql"
          ? queryPanel(options.sql, options.result)
          : table
            ? await tablePanel(table, options.offset || 0)
            : `<div class="empty welcome"><div class="empty-icon">▦</div><p class="eyebrow">YOUR DATABASE, AT A GLANCE</p><h1>A clean slate.</h1><p>Create your first table to start exploring your data.</p><a class="button" hx-get="/?view=new" hx-target="#app" href="/?view=new">＋ Create table</a></div>`;
  } catch (e) {
    content = `<div class="alert error">${esc((e as Error).message)}</div>`;
  }
  return `<aside><a class="brand" href="/"><span class="brand-icon">▥</span> Postgres<span class="brand-tag">BUN</span></a><div class="connection"><span class="status-dot"></span> Connected<span>public</span></div><a class="nav-item ${options.view === "sql" ? "active" : ""}" href="/?view=sql" hx-get="/?view=sql" hx-target="#app">⌘ <span>SQL editor</span></a><div class="sidebar-label">TABLES <span>${all.length}</span></div><nav>${all.map((t) => `<a class="nav-item ${t.name === table ? "active" : ""}" href="${esc(path(t.name))}" hx-get="${esc(path(t.name))}" hx-target="#app"><span>▦</span><span>${esc(t.name)}</span></a>`).join("") || '<p class="sidebar-empty">No tables yet</p>'}</nav><a class="new-table" href="/?view=new" hx-get="/?view=new" hx-target="#app">＋ New table</a><div class="sidebar-footer"><span class="status-dot"></span> Bun + PostgreSQL <small>Powered by htmx</small></div></aside><main><header><span>Database workspace</span><span class="runtime">Bun ${esc(Bun.version)}</span></header><div class="content">${options.notice ? `<div role="status" class="alert success">${esc(options.notice)}</div>` : ""}${options.error ? `<div role="alert" class="alert error">${esc(options.error)}</div>` : ""}${content}</div><div id="network-error" role="alert" class="alert error" hidden></div></main>`;
}

export function document(body: string) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="htmx-config" content='{"allowEval":false,"allowScriptTags":false,"historyCacheSize":0}'><title>Postgres — Database workspace</title><link rel="icon" href="data:,"><link rel="stylesheet" href="/style.css"><script src="/vendor/htmx.min.js" defer></script><script src="/app.js" defer></script></head><body><div id="app" hx-indicator="#loading" hx-disabled-elt="find button" hx-sync="#app:queue">${body}</div><div id="loading" class="htmx-indicator">Working…</div></body></html>`;
}

export function queryResult(
  rows: Record<string, unknown>[],
  count: number,
  ms: number,
) {
  const keys = rows[0] ? Object.keys(rows[0]) : [];
  return `<section class="panel query-result"><div class="panel-heading"><span>Result</span><span class="muted">${count} rows · ${ms} ms${rows.length > 500 ? " · showing first 500" : ""}</span></div>${
    keys.length
      ? `<div class="table-scroll"><table><thead><tr>${keys.map((k) => `<th>${esc(k)}</th>`).join("")}</tr></thead><tbody>${rows
          .slice(0, 500)
          .map(
            (r) =>
              `<tr>${keys.map((k) => `<td>${cell(r[k])}</td>`).join("")}</tr>`,
          )
          .join("")}</tbody></table></div>`
      : '<div class="empty">Statement completed successfully.</div>'
  }</section>`;
}
