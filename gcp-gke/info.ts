const port = Number(Deno.env.get("PORT")) || 8000;

const env = Deno.env;

Deno.serve(
    { port, onListen: () => console.log("listening on port " + port) },
    async (request: Request) => {
        const url = new URL(request.url);
        const path = url.pathname;
        if (path === "/probe") {
            const h_ = url.searchParams.get("h");
            if (!h_) return new Response("ha?", { status: 418 });
            const h = h_.startsWith("http://") ? h_ : `https://${h_}`;
            try {
                const started = performance.now();
                const probe = await fetch(h);
                const response = await probe.text();
                const elapsed = performance.now() - started;
                const msg = `${h}: ${probe.status} ${probe.statusText}, ${
                    response.length
                }, ${elapsed.toFixed(2)}ms`;
                return new Response(msg, { status: 200 });
            } catch (e) {
                return new Response(e.message, { status: 500 });
            }
        }
        return new Response(
            JSON.stringify({
                HOSTNAME: env.get("HOSTNAME"),
                VERSION: "v4",
                env: Deno.env.toObject(),
            }),
            { status: 200 }
        );
    }
);
