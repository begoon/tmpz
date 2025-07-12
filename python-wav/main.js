import WaveParser from "als-wave-parser";
import fs from "node:fs";

const BIT_RATE = 1100;
const SAMPLE_RATE = 22050;
const SAMPLES_PER_BIT = SAMPLE_RATE / BIT_RATE;
const THRESHOLD = 0x80;

console.log(`SAMPLES_PER_BIT=${SAMPLES_PER_BIT}`);

function getBit(data, i) {
    const v = data[i];
    while (i < data.length && data[i] === v) i += 1;
    if (i >= data.length) return [null, i];
    const bit = data[i] >= THRESHOLD ? 1 : 0;
    return [bit, i + Math.floor(SAMPLES_PER_BIT * 0.75)];
}

function seekSyncByte(data, i) {
    let byte = 0;
    while (true) {
        byte <<= 1;
        const [bit, advance] = getBit(data, i);
        if (bit === null) return [null, advance];
        byte = (byte | bit) & 0xff;
        if (byte === 0xe6) return [byte, advance];
        i = advance;
    }
}

function getByte(data, i) {
    let byte = 0;
    for (let j = 7; j >= 0; j--) {
        const [bit, advance] = getBit(data, i);
        if (bit === null) return [null, advance];
        byte |= bit << j;
        i = advance;
    }
    process.stdout.write(byte.toString(16).padStart(2, "0").toUpperCase() + " ");
    return [byte, i];
}

function decodeFrames(frames) {
    const data = Array.from(frames, (x) => x & 0xff);
    let i = 0;

    const [bit, advance] = seekSyncByte(data, i);
    if (bit === null) {
        console.log("sync byte (E6) not found");
        return;
    }

    console.log(`sync byte (E6) found at offset ${(advance - 1).toString(16).padStart(8, "0")}`);
    i = advance;

    let offset = 0;
    while (true) {
        if ((offset & 0x0f) === 0) {
            process.stdout.write(offset.toString(16).padStart(8, "0").toUpperCase() + " ");
        }
        const [byte, advance] = getByte(data, i);
        if (byte === null) break;
        i = advance;

        if ((offset & 0x07) === 0x07) process.stdout.write(" ");
        if ((offset & 0x0f) === 0x0f) process.stdout.write("\n");
        offset++;
    }
    console.log();
}

async function main() {
    const data = fs.readFileSync("in.wav");
    const arrayBuffer = new Uint8Array(data).buffer;
    const wav = new WaveParser(arrayBuffer);
    console.log({ ...wav, samples: undefined });
    const samples = wav.samples[0].map((x) => x * 256);
    decodeFrames(samples);
}

await main();
