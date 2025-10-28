import { fileURLToPath } from "node:url";

const url = fileURLToPath(new URL("./mastermind.wasm", import.meta.url));
console.log("loading wasm from:", url);
const { instance } = await WebAssembly.instantiateStreaming(fetch("file://" + url), {});

const h = instance.exports.init();
if (h === 0) throw new Error("game alloc/init failed");

const { deinit, remaining, tries, guess } = instance.exports;

console.log("WASM exports:", Object.keys(instance.exports));

console.log("game initialized in WASM memory");

let in_place = -1;
let by_value = -1;

let game_over = false;
while (!game_over) {
    const probe = guess(h, in_place, by_value);
    if (probe === 0) {
        console.log(`game over in ${tries(h)} tries`);
        break;
    }
    if (probe === -1) {
        console.log("no candidates left, something went wrong");
        break;
    }

    console.log(`maybe ${probe} ? (remaining ${remaining(h)})`);
    while (true) {
        const feedback = prompt(`enter feedback, <in-place> and <by-value> (e.g. "1 2"):`);
        const values = feedback
            ?.trim()
            .split(" ")
            .map((x) => parseInt(x, 10));
        if (values && values.length === 2) {
            in_place = values[0];
            by_value = values[1];
            break;
        }
        console.error('invalid input, please enter two numbers like "1 2"');
    }
}
deinit(h);
console.log("game deinitialized in WASM memory");
