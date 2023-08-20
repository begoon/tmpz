import {
    Application,
    Context,
    Router,
} from "https://deno.land/x/oak@v12.6.0/mod.ts";

const app = new Application();
const router = new Router();

const kv = await Deno.openKv();

router.get("/kv/:cmd/(.*)/values/(.*)", async (ctx: Context) => {
    let result = {};
    const { params } = ctx;
    const { cmd } = params;
    const filter = params[0].split("/");
    if (cmd == "get") {
        result.kv = await kv.get(filter);
        console.log(result.kv);
    } else if (cmd == "set") {
        result.kv = await kv.set(filter, params[1]);
    } else if (cmd == "list") {
        result.kv = {};
        console.log("filter", filter);
        const entries = kv.list({ prefix: filter });
        console.log("@");
        for await (const entry of entries) {
            console.log(entry);
            result.kv[entry.key] = entry.value;
        }
    } else {
        result.kv = { error: "unknown command " + cmd };
    }
    result.filter = filter;
    ctx.response.body = JSON.stringify({ ...ctx, RESULT: result }, null, 4);
});

app.use(router.routes());
app.use(router.allowedMethods());

const PORT = Number(Deno.env.get("PORT")) || 8000;
console.log("listening on", PORT);
await app.listen({ port: PORT });
