import { contentType } from "https://deno.land/std@0.210.0/media_types/mod.ts";
import {
    extname,
    join,
    resolve,
} from "https://deno.land/std@0.210.0/path/mod.ts";
import { Hono } from "npm:hono";
import nunjucks from "npm:nunjucks@3.2.4";

const app = new Hono({ strict: false });

const template = nunjucks.compile(`
<html>
<head>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-2">
<table class="border-collapse">
{% if parent %}
<tr>
<td colspan="6"><a href="{{ parent }}">..</a></td>
</tr>
{% endif %}
{% for file in files %}
<tr>
<td class="px-1">{{ file.icon }}</td>
<td class="px-1"><a href="{{ file.href }}" class="underline">{{ file.name }}</a></td>
<td class="px-1">{{ file.stat.size }}</td>
<td class="px-1">{{ file.type }}</td>
<td class="px-1">{{ file.stat.date }}</td>
<td class="px-1">{{ file.stat.time }}</td>
</tr>
{% endfor %}
</table>
</body>
`);

function directory(path: string) {
    const root = path === "/";
    const dir = Deno.readDirSync(path);
    const files = [];
    for (const file of dir) {
        let stat: Deno.FileInfo & { date?: string; time?: string };
        try {
            stat = Deno.statSync(resolve(join(path, file.name)));
            stat.date = stat.mtime?.toLocaleDateString();
            stat.time = stat.mtime?.toLocaleTimeString();
        } catch (_e: unknown) {
            stat = {} as Deno.FileInfo;
        }
        const href = resolve(join(FS, path, file.name));
        const icon = file.isDirectory ? "📁" : "📄";
        const type = (
            contentType(extname(file.name)) || "application/octet-stream"
        ).split("; ")[0];
        files.push({ ...file, href, stat, icon, type });
    }
    const parent = !root ? resolve(join(FS, path, "..")) : "";
    return template.render({ files, path, parent });
}

function file(path: string) {
    const type = (
        contentType(extname(path)) || "application/octet-stream"
    ).split("; ")[0];
    return { type, content: Deno.readFileSync(path) };
}

const FS = "/fs";

app.get(FS + "/*", (c) => {
    const path_ = decodeURI(c.req.path);
    const path = resolve(join("/", path_.slice(FS.length), "/"));
    const stat = Deno.statSync(path);
    if (stat.isDirectory) return c.html(directory(path));
    else {
        const { content, type } = file(path);
        return new Response(content, { headers: { "content-type": type } });
    }
});

app.get("/", (c) => c.redirect(FS));

const PORT = Number(Deno.env.get("PORT")) || 9000;

Deno.serve({
    port: PORT,
    handler: app.fetch,
    onListen: (c) => console.log(`listening on http://${c.hostname}:${c.port}`),
});
