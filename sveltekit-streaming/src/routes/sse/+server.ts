async function* streamer(): AsyncGenerator<string, void, unknown> {
    let i = 0;
    while (true) {
        i += 1;
        await new Promise((r) => setTimeout(r, 300));
        const v = { n: i, when: new Date().toISOString(), origin: "sse" };
        yield "data: " + JSON.stringify(v) + "\n\n";
    }
}

export async function GET() {
    const stream = new ReadableStream({
        async start(controller) {
            console.log("sse started");
            for await (const msg of streamer()) {
                controller.enqueue(new TextEncoder().encode(msg));
            }
        },
        async cancel() {
            console.log("sse cancelled");
        },
    });
    return new Response(stream, {
        headers: {
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    });
}
