import { handle } from "./src/app";
Bun.serve({ port: Number(process.env.PORT || 3000), fetch: handle });
