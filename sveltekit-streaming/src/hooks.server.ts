import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
    console.log("request:", event.request.method, event.url.pathname);
    console.log("headers:", event.request.headers);
    const response = await resolve(event);
    return response;
};
