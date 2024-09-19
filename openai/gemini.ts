import { argv, env } from "process";

import { GoogleGenerativeAI } from "@google/generative-ai";

const { GEMINI_API_KEY } = env;
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

const generationConfig = {
    temperature: 1,
    topP: 0.95,
    topK: 64,
    maxOutputTokens: 8192,
    responseMimeType: "text/plain",
};

async function run() {
    const session = model.startChat({ generationConfig, history: [] });
    const result = await session.sendMessage(argv.slice(2).join(" "));
    console.log(result.response.text());
}

await run();
