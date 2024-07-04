const runtime =
    typeof Deno !== "undefined"
        ? "deno " + Deno.version.deno
        : typeof Bun !== "undefined"
        ? "bun " + Bun.version
        : "maybe node";

console.log(runtime);
