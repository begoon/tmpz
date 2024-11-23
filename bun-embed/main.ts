import { file } from "bun";
import index from "./files/index.html" with { type: "file" };

export default {fetch(req) { return new Response(file(index))}};