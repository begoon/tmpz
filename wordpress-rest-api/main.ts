import { encodeBase64 } from "https://deno.land/std@0.214.0/encoding/base64.ts";
import process from "node:process";

const env = process.env;
const { WP_API, WP_API_USER, WP_API_PASSWORD } = env;

const auth = "Basic " + encodeBase64(WP_API_USER + ":" + WP_API_PASSWORD);

const customers_endpoint = WP_API + "/wc/v3/customers";

async function print(str: string) {
    await Deno.stdout.write(new TextEncoder().encode(str));
}

const needle = process.argv[2];
if (!needle) {
    console.error("please provide a username to search for.");
    process.exit(1);
}

const url = `${customers_endpoint}?search=${needle}&role=administrator`;
console.log(url);

await print(`\r\x1b[2Ksearching for "${needle}"... `);
const response = await fetch(url, {
    method: "GET",
    headers: {
        "Content-Type": "application/json",
        Authorization: auth,
    },
});

const data = (await response.json()) as {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
}[];

if (!response.ok) {
    console.error(response.statusText, data);
    process.exit(1);
}

if (!data.length) {
    console.error("not found");
    process.exit(0);
}

const { id, username, first_name, last_name, email } = data[0];
console.log(id, username, first_name, last_name, email);

const orders_endpoint = WP_API + "/wc/v3/orders";
const orders_url = `${orders_endpoint}?customer=${id}`;
const orders_response = await fetch(orders_url, {
    method: "GET",
    headers: {
        "Content-Type": "application/json",
        Authorization: auth,
    },
});

const orders_data = (await orders_response.json()) as {
    id: number;
    status: string;
    line_items: { product_id: number; name: string }[];
}[];

const orders = orders_data.map((o) => [
    o.id,
    o.status,
    o.line_items.map((i) => [i.product_id, i.name]),
]);
console.log(orders);

const password = process.argv[3];
if (password) {
    console.log("logging in...");
    const api = env.FREEMYND_API;
    const url = `${api}/user/${username}/auth`;
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_pass: password }),
    });
    if (!response.ok) {
        console.error(response.statusText);
        process.exit(1);
    }
    console.log(await response.json());
}
