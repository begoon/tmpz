// export const prerender = true;

import { env } from "$env/dynamic/private";
import { VALUE } from "$env/static/private";

export function load(): App.PageData {
    const data: App.PageData = {} as App.PageData;
    if (true) {
        data.server = { env, VALUE };
        console.log("server data", data);
    }
    return data;
}
