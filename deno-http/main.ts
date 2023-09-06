import { serveDir } from "https://deno.land/std@0.201.0/http/file_server.ts";
async function handler(req: Request): Promise<Response> {
    const pathname = new URL(req.url).pathname;
    console.log("request", req);
    if (pathname.startsWith("/static")) {
        return await serveDir(req, {
            fsRoot: ".",
            showDirListing: true,
            showIndex: true,
        });
    }
    if (req.method === "POST") {
        console.log("body", await req.json());
    }
    return new Response("OK");
}

Deno.serve(
    {
        port: 10001,
        onListen: (params) => {
            console.log(`listening on ${Deno.inspect(params)}`);
        },
    },
    handler
);
