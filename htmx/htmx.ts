import consola from "consola";
import Handlebars from "handlebars";
import * as render from "npm:preact-render-to-string";
import nunjucks from "nunjucks";

import { env } from "node:process";
import { JSX } from "preact";
import { Application, User, UserDetails } from "./tmpl.tsx";

interface HtmxRequest extends Request {
    htmx: boolean;
}

interface AuthenticatedRequest extends Request {
    username?: string;
}

interface EnrichedRequest extends HtmxRequest, AuthenticatedRequest {}

const template = nunjucks.compile(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>htmx</title>
    <script src="https://unpkg.com/htmx.org"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head>
<body>
<output class="text-4xl">{{ message }}</output>
<output>{{ username }}</output>
<br/>
<style>
    .htmx-indicator {
        opacity: 0;
        transition: opacity 500ms ease-in;
    }
    .htmx-request .htmx-indicator {
        opacity: 1;
    }
    .htmx-request.htmx-indicator {
        opacity: 1;
    }
</style>
<button 
    class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-20"
    hx-get="/pause?t=2000&r=1" hx-trigger="click" hx-indicator="#spinner"
    hx-disabled-elt="this"
>indicator</button>
<img 
    src="https://htmx.org/img/bars.svg" id="spinner" 
    class="htmx-indicator w-[10em] h-[10em] fixed left-1/2 top-1/2 z-20 -translate-x-1/2 -translate-y-1/2"
/>
<button 
    onclick='Swal.fire("Hola!");'
    class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded"
>message</button>
<div hx-get="/time" hx-trigger="load" hx-target="#time"></div>
<output id="time" class="fixed right-0 top-0 z-20 font-mono">*</output>
<div hx-get="/table" hx-trigger="load"></div>
</body>
</html>
`);

const tableTemplate = nunjucks.compile(`
<table>
    <thead class="border bg-gray-100 sticky top-0 z-10">
        <tr>
            <th>name</th>
            <th>value</th>
        </tr>
    </thead>
    <tbody>
    {% for name, value in rows %}
        <tr class="align-top">
            <td>{{ name }}</td>
            <td class="
                w-full break-all hover:bg-gray-100 
            ">
                <span class="relative">
                    <span class="
                        hover:before:content-['&raquo;']
                        hover:after:content-['&laquo;']
                        hover:before:absolute
                        hover:before:-left-4 hover:before:top-auto
                        hover:after:absolute
                        hover:after:-right-4 hover:after:top-auto
                        hover:outline hover:outline-green-500
                        inline-block
                    ">
                        {{ value }}
                    </span>
                 </span>
             </td>
        </tr>
    {% endfor %}
    </tbody>
</table>
`);

Handlebars.registerPartial("NamePartial", ({ arg }) => {
    console.log({ arg });
    return arg;
});

const handlebarsTemplate = Handlebars.compile(
    [
        "name: {{>NamePartial arg=name}}",
        "name: {{>NamePartial arg='htmx'}}",
    ].join(", ")
);

async function handler(request: EnrichedRequest): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const context = {
        message: "OK",
        username: request.username,
    };
    if (pathname === "/tsx") {
        const q = url.searchParams.get("q");
        let page: JSX.Element;
        if (q) page = User({ name: `tsx/${Number(q) + 1}`, q: Number(q) + 1 });
        else {
            const child = UserDetails({ initial: "initial/name" });
            page = Application(child);
        }
        return new Response(render.renderToString(page), {
            headers: { "Content-Type": "text/html" },
        });
    }
    if (pathname === "/hbs") {
        const name = url.searchParams.get("name") || "htmx";
        return new Response(handlebarsTemplate({ name }));
    }
    if (pathname === "/indicator") {
        return new Response("OK", {
            headers: { "Cache-Control": "no-store" },
        });
    }
    if (pathname === "/table") {
        const rows = Object.entries(env).sort(
            ([a], [b]) => -a.localeCompare(b)
        );
        rows.push(["htmx", Boolean(request.htmx).toString()]);
        rows.push(["username", request.username || "anonymous"]);
        return new Response(tableTemplate.render({ rows }), {
            headers: { "Content-Type": "text/html" },
        });
    }
    if (pathname === "/time") {
        context.message = new Date().toString();
        return new Response(new Date().toISOString());
    }
    if (pathname === "/z") {
        return new Response(template.render(context), {
            headers: { "Content-Type": "text/html" },
        });
    }
    if (pathname === "/pause") {
        const url = new URL(request.url);
        const t = Number(url.searchParams.get("t")) || 500;
        const r = Boolean(url.searchParams.get("r"));
        console.info("pause", t);
        await new Promise((resolve) => setTimeout(resolve, t));
        return r
            ? new Response(`paused for ${t}s`)
            : Response.json({ message: "paused", duration: t });
    }
    if (pathname === "/delay") {
        const t = Number(new URL(request.url).searchParams.get("t")) || "0.5";
        console.info("delay", t);
        const response = await fetch(`https://httpbin.org/delay/${t}`);
        console.log("delayed", response.status);
        return Response.json({ message: "delayed", duration: t });
    }
    if (pathname === "/error") {
        throw new Error("oops");
    }
    if (pathname === "/env") {
        return new Response(JSON.stringify(env), {
            headers: { "Content-Type": "application/json" },
        });
    }
    return Response.json({ status: "ha?" });
}

async function cors(request: EnrichedRequest, next: Handler) {
    const response = await next(request);
    response.headers.set("Access-Control-Allow-Origin", "*");
    response.headers.set(
        "Access-Control-Allow-Methods",
        "GET, POST, PUT, DELETE, OPTIONS"
    );
    response.headers.set("Access-Control-Allow-Headers", "Content-Type");
    response.headers.set("Access-Control-Max-Age", "86400");
    return response;
}

async function htmx(request: EnrichedRequest, next: Handler) {
    request.htmx = Boolean(request.headers.get("HX-Request"));
    const res = await next(request);
    return res;
}

async function basic(request: EnrichedRequest, next: Handler) {
    const pathname = new URL(request.url).pathname;
    if (pathname === "/z") {
        const auth = request.headers.get("Authorization");
        if (auth) {
            const [type, credentials] = auth.split(" ");
            if (type.toLowerCase() === "basic") {
                const [username, password] = atob(credentials).split(":");
                if (username === "wheel" && password === "ha?") {
                    request.username = username;
                    return await next(request);
                }
            }
        }
        return new Response(null, {
            status: 401,
            headers: { "WWW-Authenticate": 'Basic realm="protected"' },
        });
    }
    return await next(request);
}

async function bearer(request: EnrichedRequest, next: Handler) {
    const pathname = new URL(request.url).pathname;
    if (pathname === "/env") {
        const auth = request.headers.get("Authorization");
        if (auth) {
            const [type, token] = auth.split(" ");
            if (type.toLowerCase() === "bearer") {
                if (token === "tea") return next(request);
            }
        }
        return new Response(null, { status: 401 });
    }
    return await next(request);
}

async function tracer(request: EnrichedRequest, next: Handler) {
    const started = performance.now();
    const pathname = new URL(request.url).pathname;
    if (pathname !== "/ws") consola.info("REQUEST", request.method, pathname);
    const response = await next(request);
    if (pathname !== "/ws")
        consola.info(
            "RESPONSE",
            pathname,
            response.status,
            (performance.now() - started).toFixed(2)
        );
    return response;
}

async function exception(request: EnrichedRequest, next: Handler) {
    try {
        return await next(request);
    } catch (error) {
        let message = "unknown error";
        if (error instanceof Error) {
            consola.error(error);
            message = error.message;
        }
        return new Response(message, { status: 500 });
    }
}

async function timed(request: EnrichedRequest, handler: Handler) {
    const f = async () => await handler(request);
    let timer;
    const timeout = 1000;
    const limiter = new Promise<Response>((_, reject) => {
        timer = setTimeout(
            () =>
                reject(
                    Response.json(
                        {
                            error: "timeout",
                            pathname: request.url,
                        },
                        { status: 408 }
                    )
                ),
            timeout
        );
    });

    try {
        return await Promise.race<Response>([f(), limiter]);
    } catch (error) {
        return error as Response;
    } finally {
        clearTimeout(timer);
    }
}

type Handler = (req: EnrichedRequest) => Promise<Response>;
type Middleware = (req: EnrichedRequest, next: Handler) => Promise<Response>;

const MIDDLEWARES: Middleware[] = [
    exception,
    tracer,
    // timed,
    htmx,
    basic,
    bearer,
    cors,
];

function middlewares(handler: Handler): Handler {
    for (const middleware of MIDDLEWARES.toReversed()) {
        const next = handler;
        handler = async (request) => await middleware(request, next);
    }
    return handler;
}

const PORT = Number(env.PORT) || 8000;

async function serve(request: Request) {
    return await middlewares(handler)(request as EnrichedRequest);
}

if (typeof Deno !== "undefined") {
    Deno.serve(
        { port: PORT, onListen: () => consola.info(`ready on port ${PORT}`) },
        serve
    );
}

// if (typeof Bun !== "undefined") Bun.serve({ port: PORT, fetch: serve });
