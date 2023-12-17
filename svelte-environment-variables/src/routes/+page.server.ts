import { env as dynamic_public_env } from "$env/dynamic/public";
import { VAR_STATIC_PUBLIC } from "$env/static/public";

import { env as dynamic_private_env } from "$env/dynamic/private";
import { VAR_STATIC_PRIVATE } from "$env/static/private";

function vars(v: any) {
    Object.keys(v).forEach((k) => {
        if (!k.startsWith("VAR_")) delete v[k];
    });
    return v;
}

export function load() {
    const data = {
        dynamic_public_env: vars(dynamic_public_env),
        VAR_STATIC_PUBLIC,
        dynamic_private_env: vars(dynamic_private_env),
        VAR_STATIC_PRIVATE,
    };
    console.log("data", data);
    return data;
}
