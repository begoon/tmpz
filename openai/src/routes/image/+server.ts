import { json } from "@sveltejs/kit";
import fs from "fs";
import * as openai from "./openai-image";

export async function POST({ request }) {
    const { model, query } = await request.json();
    console.log({ model, query });

    const image = await openai.create(model, query);

    if (!image) throw new Error("image not found");

    console.log(image);
    await saveImage(image);

    return json({ image });
}

async function saveImage(url: string) {
    const response = await fetch(url);
    const binary = await response.arrayBuffer();
    const now = new Date().toISOString().replace("Z", "").replace("T", "-");
    const name = "image-" + now + ".jpg";
    fs.writeFileSync("images/" + name, Buffer.from(binary));
    console.log("image saved", { name, url, sz: binary.byteLength });
}
