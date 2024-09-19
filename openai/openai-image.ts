import process from "process";

import OpenAI from "openai";

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

const query = process.argv.slice(2).join(" ");

async function main() {
    const response = await openai.images.generate({
        model: "dall-e-3",
        prompt: query,
        n: 1,
        size: "1024x1024",
    });
    console.log(response.data);
    const image_url = response.data[0].url;
    console.log(image_url);
}

main();
