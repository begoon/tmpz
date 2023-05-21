import { json } from '@sveltejs/kit';

/** @type {import('./$types').RequestHandler} */
export async function POST({ request}) {
    const data = await request.json();
    let query = {};
    const entries = new URL(request.url).searchParams.entries();
    for (let [key, value] of entries) {
        query[key] = value;
    }
    return json({
        request: data,
        query: query,
        url: request.url,
        env: process.env
    });
}
