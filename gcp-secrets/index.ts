import process from "npm:process";

const port = process.env.PORT || 8000;

Deno.serve(
    { port, onListen: () => console.log("listening on port " + port) },
    (_req: Request): Response => {
        const secret = process.env.K_SERVICE
            ? Deno.readTextFileSync("/secrets/ephemeral-secret")
            : "?";
        return new Response(JSON.stringify({ secret, env: process.env }), {
            headers: { "content-type": "application/json" },
        });
    }
);
