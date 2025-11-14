import { error, json } from "@sveltejs/kit";

export async function GET({ request }) {
    const q = new URL(request.url).searchParams.get("q");
    if (q === "*error") throw new Error("data/error", { cause: 69 });
    if (q === "*404") return new Response(JSON.stringify({ x: "data/404" }), { status: 404 });
    if (q === "*500") error(500, "data/500");
    if (q === "*pause") await new Promise((resolve) => setTimeout(resolve, 3000));
    return json({ when: new Date().toISOString(), q });
}
