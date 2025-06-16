import { serveDir } from "jsr:@std/http/file-server";
Deno.serve((req: Request) => serveDir(req, { fsRoot: "." }));
