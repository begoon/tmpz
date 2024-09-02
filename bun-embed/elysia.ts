import { Elysia } from "elysia";
import { swagger } from "@elysiajs/swagger";

new Elysia()
    .use(swagger())
    .get("/", () => "hi")
    .post("/hello", () => "world")
    .listen(3000);
