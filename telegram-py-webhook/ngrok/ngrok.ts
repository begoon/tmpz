import { mergeReadableStreams } from "https://deno.land/std@0.211.0/streams/merge_readable_streams.ts";
import { TextLineStream } from "https://deno.land/std@0.211.0/streams/text_line_stream.ts";

export type NgrokOptions = {
    protocol: string;
    port: number;
};

export async function* connect(options: NgrokOptions) {
    const process = new Deno.Command("ngrok", {
        args: [options.protocol, options.port.toString(), "--log=stdout"],
        stdin: "piped",
        stdout: "piped",
        stderr: "piped",
    }).spawn();
    process.stdin?.close();

    const output = mergeReadableStreams(process.stdout, process.stderr)
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(new TextLineStream());

    const ready = /started tunnel.*:\/\/(.*)/;
    for await (const line of output) {
        const connected = line.match(ready);
        if (connected) {
            const url = connected[1];
            console.log("ngrok connected", { url });
            yield connected[1];
        }
    }
    console.log("ngrok exited");
}
