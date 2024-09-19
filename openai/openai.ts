import process from "process";

import OpenAI from "openai";

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

const query = process.argv.slice(2).join(" ");

const completion = await openai.chat.completions.create({
    messages: [{ role: "user", content: query }],
    model: "gpt-4o-mini",
});

console.log(completion.choices[0].message.content);
