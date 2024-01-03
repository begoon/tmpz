import { readLines } from "./read_lines.ts";

export async function* shell(cmd: string) {
    const [target, ...args] = cmd.split(" ");
    const command = new Deno.Command(target, {
        args,
        stdin: "piped",
        stdout: "piped",
    });
    const process = command.spawn();
    for await (const line of readLines(process.stdout)) yield line;
}
