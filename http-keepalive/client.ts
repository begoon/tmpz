import process from "node:process";
const HOST = "http://localhost:8000";

async function performRequests() {
    const paths = ["/get", "/ip", "/headers"];

    try {
        for (const path of paths) {
            const url = `${HOST}${path}`;
            const headers = new Headers({ Connection: "keep-alive" });
            const response = await fetch(url, { headers });
            const data = await response.json();
            console.log(`response for ${path}:`, data);
            const pause = Number(process.env.PAUSE || "500");
            await new Promise((resolve) => setTimeout(resolve, pause));
        }
    } catch (e) {
        const error = e as Error;
        console.error("error:", error.message);
    }
}

await performRequests();
