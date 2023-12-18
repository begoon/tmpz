// export const prerender = true;

import { env } from "$env/dynamic/public";
import { VALUE } from "$env/static/public";

export function load({ data }: { data: App.PageData }) {
    data.client = { env, VALUE };
    console.log("client load", data);
    return data;
}
