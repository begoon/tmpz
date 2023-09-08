import { serveDir } from "https://deno.land/std@0.201.0/http/file_server.ts";
import nunjucks from "npm:nunjucks";

const kv = await Deno.openKv();

const queue: string[] = [];

const queueTemplate = nunjucks.compile(`
{% if controller %}
sse connected
{% else %}
sse disconnected
{% endif %}
{% for v in queue|reverse %}
<li>{{ v }}</li>
{% endfor %}
<span id="when" hx-swap-oob="true">updated at {{now}}</span>
`);

const enqueuedTemplate = nunjucks.compile(`
<span _="on load wait 5s then transition opacity to 0 then remove me">
    enqueued at {{when}}
</span>
`);

const receivedTemplate = nunjucks.compile(`
    <div _="on load wait 5s then transition opacity to 0 then remove me">
        <mark>message</mark>
        <b>{{message}}</b>
    </div>
`);

import {
    HumanizeDuration,
    HumanizeDurationLanguage,
} from "npm:humanize-duration-ts";

const humanizer = new HumanizeDuration(new HumanizeDurationLanguage());

let controller: ReadableStreamDefaultController<Uint8Array> | undefined;

async function handler(req: Request): Promise<Response> {
    const pathname = new URL(req.url).pathname;
    console.log("pathname", pathname);
    if (pathname === "/env")
        return new Response(JSON.stringify({ env: Deno.env.toObject() }));
    if (pathname === "/sse") {
        kv.listenQueue((value_) => {
            if (!controller) return;
            const value = <Message>value_;
            const now = new Date();
            const delay = humanizer.humanize(
                now.getTime() - new Date(value.when).getTime()
            );
            const message = `received at ${now.toISOString()} [delivered in ${delay}] "${
                value.message
            }"`;
            console.log(message);
            const formatted = receivedTemplate
                .render({ now, delay, message })
                .replaceAll("\n", "");
            controller.enqueue(
                new TextEncoder().encode(`data: ${formatted}\r\n\r\n`)
            );
            queue.push(message);
        });

        const stream = new ReadableStream({
            start(controller_) {
                console.log("sse started");
                controller = controller_;
            },
            cancel: () => {
                console.log("sse closed");
                controller = undefined;
            },
        });
        return new Response(stream, {
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-store",
                "X-Accel-Buffering": "no",
            },
        });
    }

    if (req.method === "POST" && pathname === "/enqueue") {
        const form = await req.formData();
        const message = form.get("message");
        console.log("enqueued", message);

        const when = new Date().toISOString();
        await kv.enqueue({ message, when });

        return new Response(enqueuedTemplate.render({ when }));
    }
    if (pathname === "/health") return new Response("OK");
    if (pathname === "/queue")
        return new Response(
            queueTemplate.render({
                controller,
                queue,
                now: new Date().toISOString(),
            })
        );

    return await serveDir(req, {
        fsRoot: ".",
        showDirListing: true,
        showIndex: true,
    });
}

type Message = {
    when: Date;
    message: string;
};

setTimeout(async () => {
    await kv.enqueue({
        when: new Date().toISOString(),
        message: "initial " + new Date().toISOString(),
    });
}, 1000);

Deno.serve(
    {
        port: Number(Deno.env.get("PORT")) || 10001,
        onListen: (params) => console.log(`ready on ${Deno.inspect(params)}`),
    },
    handler
);
