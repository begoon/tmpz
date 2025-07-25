import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

function hex(n, width) {
    return n.toString(16).toUpperCase().padStart(width, "0");
}

function dump_file(name) {
    let start = 0,
        end = 0,
        entry = 0;

    assert.ok(name.includes("."), `Name '${name}'`);

    const contents = fs.readFileSync("src/files" + name);
    const sz = contents.length;

    const ext = path.extname(name);

    let n = 0;

    // If the file name starts with "mon" this is an image of Monitor
    // (no sync-byte, start and end addresses at front).
    if (ext === ".bin" || ext === ".COM") {
        if (name.startsWith("mon")) {
            end = 0xffff;
            start = end - sz + 1;
            entry = 0xf800;
        } else if (ext === ".COM") {
            start = 0x100;
            end = start + sz - 1;
            entry = start;
        } else {
            end = sz - 1;
            start = 0;
            entry = 0;
        }
    } else {
        // Is it the sync-byte (E6)?
        if (contents[n] == 0xe6) n += 1;

        // start address
        start = (contents[n] << 8) | contents[n + 1];
        n += 2;

        // end address
        end = (contents[n] << 8) | contents[n + 1];
        n += 2;

        entry = start;
    }

    console.log(`files['${name}'] = {`);
    console.log(`start: 0x${hex(start, 4)},`);
    console.log(`end: 0x${hex(end, 4)},`);
    console.log(`entry: 0x${hex(entry, 4)},`);
    console.log(`image:`);

    let line = '"';
    let i = 0;
    while (start <= end) {
        assert.ok(n < sz, `n = ${n}, sz = ${sz}, start = ${start}, end = ${end}`);
        let c = contents[n];
        n += 1;
        line += "\\x" + hex(c, 2);
        i += 1;
        if (i >= 32) {
            i = 0;
            line += '"';
            if (start < end) line += ' +\n"';
        }
        ++start;
    }
    if (i > 0) line += '"';
    line += "\n};\n\n";
    console.log(line);
}

function preloaded_files() {
    console.log("function preloaded_files() {");
    console.log("files = [];\n");

    for (const file of fs.readdirSync("files")) {
        if (!file) continue;
        dump_file(file);
    }

    console.log("return files;");
    console.log("}\n");
}

function tape_catalog() {
    console.log("export function tape_catalog() {");
    console.log("  return [");
    for (const file of fs.readdirSync("files").toSorted()) {
        if (!file) continue;
        console.log(`    "${file}",`);
    }
    console.log("  ];");
    console.log("}");
}

function main() {
    if (process.argv[2] === "preloaded") return preloaded_files();

    const filename = process.argv[3];
    if (process.argv[2] === "dump" && filename) return dump_file(filename);

    if (process.argv[2] === "tape") return tape_catalog();
}

main();
