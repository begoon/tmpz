import { shell } from "./shell.ts";

const cmd = "ngrok http 8080 --log=stdout";

const ready = /started tunnel.*:\/\/(.*)/;

for await (const line of shell(cmd)) {
    console.log(line);
    const match = line.match(ready);
    if (match) {
        const url = match[1];
        console.log(`tunnel ready: ${url}`);
    }
}
