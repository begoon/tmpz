import process from "process";

import OpenAI from "openai";

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

const chatCompletion = await openai.chat.completions.create({
    model: "gpt-3.5-turbo-instruct",
    prompt: "can gemini generate images from text?",
    temperature: 1,
    max_tokens: 2048,
    top_p: 1,
    frequency_penalty: 0,
    presence_penalty: 0,
});
