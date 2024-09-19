import OpenAI from "openai";

import { env } from "$env/dynamic/private";

const openai = new OpenAI({
    apiKey: env.OPENAI_API_KEY,
});

export async function create(model: string, prompt: string) {
    console.log("create", { model, prompt });
    const response = await openai.images.generate({
        model,
        prompt,
        n: 1,
        size: "1024x1024",
    });
    console.log(response.data);
    return response.data[0].url;
}

export async function kreate(model: string, prompt: string) {
    console.log("kcreate", { model, prompt });
    return new Promise<string>((resolve, reject) => {
        setTimeout(() => {
            const seed = Math.random().toString(36).substring(7);
            resolve(`https://picsum.photos/seed/${seed}/1024/1024`);
        }, 4000);
    });
}
