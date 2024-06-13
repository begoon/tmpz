const port = Number(Deno.env.get("PORT")) || 8000;

const env = Deno.env;

Deno.serve(
    { port, onListen: () => console.log("listening on port " + port) },
    async (_req: Request) => {
        return new Response(
            JSON.stringify({
                HOSTNAME: env.get("HOSTNAME"),
                VERSION: "v3",
                env: Deno.env.toObject(),
            }),
            { status: 200 }
        );
    }
);
