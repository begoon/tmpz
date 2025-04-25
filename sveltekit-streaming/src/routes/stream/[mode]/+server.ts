type Mode = "raw" | "sse";

async function* streamer(mode: Mode): AsyncGenerator<string, void, unknown> {
    let i = 0;
    const pause = mode == "sse" ? 300 : 800;
    while (true) {
        i += 1;
        await new Promise((r) => setTimeout(r, pause));
        const v = { n: i, when: new Date().toISOString(), mode };
        if (mode == "sse") yield "data: " + JSON.stringify(v) + "\n\n";
        else yield JSON.stringify(v) + "\n";
    }
}

export async function GET({ params }) {
    const mode = (params.mode as Mode) == "sse" ? "sse" : "raw";
    console.log(`[${mode}] stream requested`);

    const stream = new ReadableStream({
        async start(controller) {
            console.log(`[${mode}] stream started`);
            for await (const msg of streamer(mode)) {
                controller.enqueue(new TextEncoder().encode(msg));
            }
        },
        async cancel() {
            console.log(`[${mode}] stream cancelled`);
        },
    });
    const contentType = mode == "sse" ? "text/event-stream" : "application/json";
    return new Response(stream, {
        headers: {
            "Content-Type": contentType,
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    });
}
