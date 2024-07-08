function generateStream(): ReadableStream<Uint8Array> {
    let count = 0;
    let controller: ReadableStreamDefaultController<Uint8Array>;
    const interval = setInterval(() => {
        if (count > 3) {
            controller.close();
            clearInterval(interval);
        } else {
            const data = count < 3 ? `chunk ${count}` : "";
            count += 1;
            const size = data.length.toString(16);
            const raw = new Uint8Array([
                ...new TextEncoder().encode(size),
                0x0d,
                0x0a,
                ...new TextEncoder().encode(data),
                0x0d,
                0x0a,
            ]);
            controller.enqueue(raw);
            console.log(`sent: ${count}: ${raw}`);
        }
    }, 1000);

    return new ReadableStream({
        start(controller_) {
            controller = controller_;
        },
        cancel() {
            clearInterval(interval);
        },
    });
}

async function handler(req: Request): Promise<Response> {
    const stream = generateStream();
    return new Response(stream, {
        status: 200,
        headers: {
            "Content-Type": "text/plain",
            "Transfer-Encoding": "chunked",
            "X-Content-Type-Options": "nosniff",
        },
    });
}

await Deno.serve({ port: 8000 }, handler);
