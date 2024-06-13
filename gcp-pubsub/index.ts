const port = Number(Deno.env.get("PORT")) || 8000;

Deno.serve(
    { port, onListen: () => console.log("listening on port " + port) },
    async (req: Request) => {
        console.log(req.url, req);
        if (req.method !== "POST") return new Response("tea?", { status: 418 });

        const dlq = req.url.includes("dlq");
        console.log({ dlq });

        const text = await req.text();
        console.log({ text });

        if (!dlq) console.log(JSON.parse(text));
        return new Response("", { status: 200 });
    }
);
