import chalk from "npm:chalk";
const {
    bold: { red, green, white },
} = chalk;

console.log("handler", white("initialized"));

export async function handler(event: Response) {
    console.log("HANDLER", event);

    const request = await event.json();
    console.log({ request });

    return "ALIVE";
}
