import { Hono } from "hono";
import { serveStatic } from "hono/deno";

const kv = await Deno.openKv();
await kv.set(["booted"], new Date().toISOString());

type Variables = {
  htmx: boolean;
};

const app = new Hono<{ Variables: Variables }>();

app.use(async (c, next) => {
  c.set("htmx", Boolean(c.req.header("HX-Request")));
  await next();
});

const cleanDate = (date?: string) => date?.replace("T", " ").split(".")[0];

async function info() {
  const when = cleanDate((await kv.get(["booted"])).value as string);
  return (
    <div class="fixed top-0 right-0 bg-gray-200 text-[0.7rem] *:px-1">
      <span>
        <b>htmx</b>/
        <script>document.write(htmx.version)</script>
      </span>
      <span>
        <b>boot</b>/{when}
      </span>
    </div>
  );
}

app.delete("/delete/:key", async (c) => {
  const key = c.req.param("key");
  console.log("delete", key);
  const { value } = await kv.get([key]);
  await kv.delete([key]);
  return c.html(item(key, value));
});

app.get("/create", (c) => {
  return c.html(
    <tr>
      <td>
        <input
          type="text"
          name="key"
          placeholder="key"
          class="bg-gray-200"
          hx-get="/check"
          hx-trigger="change, keyup, delay:500ms"
        />
      </td>
      <td>
        <input
          type="text"
          name="value"
          placeholder="value"
          class="bg-gray-200"
        />
      </td>
      <td>
        <button
          class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded"
          hx-post="/create"
          hx-target="tr"
          hx-swap="outerHTML"
        >
          save
        </button>
      </td>
    </tr>,
  );
});

function item(key: string, value: unknown, i: number | undefined = undefined) {
  const deleted = i === undefined;
  const classes = ["*:pr-4", "py-2"];
  if (deleted) classes.push("line-through");
  return (
    <tr
      class={classes.join(" ")}
      {...(i !== undefined ? { id: `item-${i}` } : {})}
    >
      <td>{key}{deleted}</td>
      <td>{value}</td>
      <td>
        {deleted
          ? (
            <button class="disabled bg-gray-500 text-white font-bold py-1 px-2 rounded cursor-not-allowed">
              deleted
            </button>
          )
          : (
            <button
              class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
              hx-delete={`/delete/${key}`}
              hx-target={`#item-${i}`}
              hx-swap="outerHTML"
            >
              delete
            </button>
          )}
      </td>
    </tr>
  );
}

app.get("/", async (c) => {
  const htmx = c.get("htmx");
  console.log({ htmx });
  const items = [];
  let i = 0;
  for await (const entry of kv.list({ prefix: [] })) {
    const { key, value } = entry;
    items.push(item(key.join("-"), value, i));
    i += 1;
  }
  return c.html(
    <>
      <html>
        <head>
          <meta charset="UTF-8" />
          <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
          />
          <title>htmx/kv</title>
          <script src="https://unpkg.com/htmx.org@2.0.4"></script>
          <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body>
          {await info()}
          <table class="text-left">
            <thead id="header">
              <tr class="bg-gray-200">
                <th>key</th>
                <th>value</th>
                <th>
                  <button
                    class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded"
                    hx-get={`/create`}
                    hx-target="#header"
                    hx-swap="beforebegin"
                  >
                    create
                  </button>
                </th>
              </tr>
            </thead>
            {items}
          </table>
        </body>
      </html>
    </>,
  );
});

app.get("/version", (c) => c.text(Deno.version.deno));

app.get("*", serveStatic({ root: "./static" }));

Deno.serve(app.fetch);
