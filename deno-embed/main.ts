import { serveDir } from "jsr:@std/http/file-server";
Deno.serve((req: Request) => serveDir(req, { fsRoot: import.meta.dirname + "/files" }));
