import consola from "consola";
import nunjucks from "nunjucks";

import { env } from "node:process";

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
</head>
<body>
<output class="text-4xl">{{ message }}</output>
<output>{{ username }}</output>
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

function handler(request: EnrichedRequest): Response {
    const pathname = new URL(request.url).pathname;
    const context = {
        message: "OK",
        username: request.username,
    };
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

function cors(request: EnrichedRequest, next: Handler): Response {
    const response = next(request);
    response.headers.set("Access-Control-Allow-Origin", "*");
    response.headers.set(
        "Access-Control-Allow-Methods",
        "GET, POST, PUT, DELETE, OPTIONS"
    );
    response.headers.set("Access-Control-Allow-Headers", "Content-Type");
    response.headers.set("Access-Control-Max-Age", "86400");
    return response;
}

function htmx(request: EnrichedRequest, next: Handler): Response {
    request.htmx = Boolean(request.headers.get("HX-Request"));
    return next(request);
}

function basic(request: EnrichedRequest, next: Handler): Response {
    const pathname = new URL(request.url).pathname;
    if (pathname === "/z") {
        const auth = request.headers.get("Authorization");
        if (auth) {
            const [type, credentials] = auth.split(" ");
            if (type.toLowerCase() === "basic") {
                const [username, password] = atob(credentials).split(":");
                if (username === "wheel" && password === "ha?") {
                    request.username = username;
                    return next(request);
                }
            }
        }
        return new Response(null, {
            status: 401,
            headers: { "WWW-Authenticate": 'Basic realm="protected"' },
        });
    }
    return next(request);
}

function bearer(request: EnrichedRequest, next: Handler): Response {
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
    return next(request);
}

function tracer(request: EnrichedRequest, next: Handler): Response {
    const started = performance.now();
    const pathname = new URL(request.url).pathname;
    consola.info("REQUEST", request.method, pathname);
    const response = next(request);
    consola.info(
        "RESPONSE",
        request.url,
        response.status,
        (performance.now() - started).toFixed(2)
    );
    return response;
}

function exception(request: EnrichedRequest, next: Handler): Response {
    try {
        return next(request);
    } catch (error) {
        let message = "unknown error";
        if (error instanceof Error) {
            consola.error(error);
            message = error.message;
        }
        return new Response(message, { status: 500 });
    }
}

type Handler = (request: EnrichedRequest) => Response;

const MIDDLEWARES = [exception, tracer, htmx, basic, bearer, cors];

function middlewares(handler: (request: EnrichedRequest) => Response): Handler {
    for (const middleware of MIDDLEWARES.reverse()) {
        const next = handler;
        handler = (request) => middleware(request, next);
    }
    return handler;
}

const PORT = Number(env.PORT) || 8000;

function serve(request: Request): Response {
    return middlewares(handler)(request as EnrichedRequest);
}

if (typeof Deno !== "undefined") {
    Deno.serve(
        { port: PORT, onListen: () => consola.info(`ready on port ${PORT}`) },
        serve
    );
}

// if (typeof Bun !== "undefined") Bun.serve({ fetch: serve });
