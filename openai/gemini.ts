import { argv, env } from "process";

import { GoogleGenerativeAI } from "@google/generative-ai";

const { GEMINI_API_KEY } = env;
const client = new GoogleGenerativeAI(GEMINI_API_KEY);

const model = client.getGenerativeModel({ model: "gemini-1.5-flash" });

const generationConfig = {
    temperature: 1,
    topP: 0.95,
    topK: 64,
    maxOutputTokens: 8192,
    responseMimeType: "text/plain",
};

async function query(question: string) {
    const session = model.startChat({ generationConfig, history: [] });
    const result = await session.sendMessage(question);
    return result.response.text();
}

console.log(await query(argv.slice(2).join(" ")));
