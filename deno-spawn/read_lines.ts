export async function* readLines(stream: ReadableStream) {
    for await (const chunk of stream) {
        for await (const line of splitLines(chunk)) yield line;
    }
}

async function* splitLines(chunk: Uint8Array) {
    const textDecoder = new TextDecoder();
    let incomplete = "";
    const text = textDecoder.decode(chunk);
    const lines = text.split("\n");
    if (lines.length === 1) incomplete += lines[0];
    else if (lines.length > 1) {
        yield incomplete + lines[0];
        for (let i = 1; i < lines.length - 1; i++) yield lines[i];
        incomplete = lines.at(-1)!;
    }
}
