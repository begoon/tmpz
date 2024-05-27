import { readLines } from "./read_lines.ts";

export async function* shell(cmd: string, args: string[] = []) {
    const command = new Deno.Command(cmd, {
        args,
        stdin: "piped",
        stdout: "piped",
    });
    const process = command.spawn();
    for await (const line of readLines(process.stdout)) yield line;
    console.log("shell", cmd, "exited");
}
