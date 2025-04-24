async function* streamer(): AsyncGenerator<string, void, unknown> {
    let i = 0;
    while (true) {
        i += 1;
        await new Promise((r) => setTimeout(r, 1000));
        const v = { n: i, when: new Date().toISOString(), origin: "stream" };
        yield JSON.stringify(v) + "\n";
    }
}

export async function GET() {
    const stream = new ReadableStream({
        async start(controller) {
            console.log("stream started");
            for await (const msg of streamer()) {
                controller.enqueue(new TextEncoder().encode(msg));
            }
        },
        async cancel() {
            console.log("stream cancelled");
        },
    });
    return new Response(stream, {
        headers: {
            "Content-Type": "application/json",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    });
}
