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

function decodeData(frames) {
    const data = Array.from(frames, (x) => x & 0xff);
    let i = 0;

    const [bit, advance] = seekSyncByte(data, i);
    if (bit === null) {
        console.log("sync byte (E6) not found");
        return;
    }

    console.log(`sync byte (E6) found at offset ${(advance - 1).toString(16).padStart(8, "0")}`);
    i = advance;

    const result = [];
    let offset = 0;
    while (true) {
        if ((offset & 0x0f) === 0) {
            process.stdout.write(offset.toString(16).padStart(8, "0").toUpperCase() + " ");
        }
        const [byte, advance] = getByte(data, i);
        if (byte === null) break;
        i = advance;

        result.push(byte);

        if ((offset & 0x07) === 0x07) process.stdout.write(" ");
        if ((offset & 0x0f) === 0x0f) process.stdout.write("\n");
        offset++;
    }
    console.log();
    return result;
}

const hex = (v) =>
    v
        .toString(16)
        .padStart(v > 255 ? 4 : 2, "0")
        .toUpperCase();

function rk86_check_sum(v) {
    let sum = 0;
    let j = 0;
    while (j < v.length - 1) {
        const c = v[j];
        sum = (sum + c + (c << 8)) & 0xffff;
        j += 1;
    }
    const sum_h = sum & 0xff00;
    const sum_l = sum & 0xff;
    sum = sum_h | ((sum_l + v[j]) & 0xff);
    return sum;
}

async function main() {
    const input = fs.readFileSync("in.wav");
    const arrayBuffer = new Uint8Array(input).buffer;
    const wav = new WaveParser(arrayBuffer);
    console.log({ ...wav, samples: undefined });
    const data = wav.samples[0].map((x) => x * 256);
    const decoded = decodeData(data);

    const start = decoded[1] | (decoded[0] << 8);
    const end = decoded[3] | (decoded[2] << 8);
    const size = end - start + 1;
    console.log(`${hex(start)}-${hex(end)}`, hex(size));

    const trailer_0000 = decoded[4 + size] | (decoded[4 + size + 1] << 8);
    const trailer_e6 = decoded[4 + size + 2];
    console.log(hex(trailer_0000), hex(trailer_e6));
    if (trailer_0000 !== 0x0000) throw new Error(`trailer_0000=${hex(trailer_0000)} != 0000`);
    if (trailer_e6 !== 0xe6) throw new Error(`trailer_e6=${hex(trailer_e6)} != E6`);

    const checksum = decoded[4 + size + 2 + 2] | (decoded[4 + size + 2 + 1] << 8);
    console.log(`checksum=${hex(checksum)}`);
    const actual_checksum = rk86_check_sum(decoded.slice(4, 4 + size));

    if (actual_checksum !== checksum) {
        throw new Error(`actual_checksum=${hex(actual_checksum)} != checksum=${hex(checksum)}`);
    }
}

await main();
