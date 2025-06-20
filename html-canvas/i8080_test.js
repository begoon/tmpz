import process from "node:process";

const RED = (v) => "\x1b[31m" + v + "\x1b[0m";
const GREEN = (v) => "\x1b[32m" + v + "\x1b[0m";
const LIGHT_GREEN = (v) => "\x1b[92m" + v + "\x1b[0m";
const YELLOW = (v) => "\x1b[33m" + v + "\x1b[0m";
const BLUE = (v) => "\x1b[34m" + v + "\x1b[0m";

function Memory() {
    this.mem = new Array(0x10000).fill(0);

    this.read = (addr) => this.mem[addr & 0xffff] & 0xff;
    this.write = (addr, w8) => (this.mem[addr & 0xffff] = w8 & 0xff);

    /**
     * @param {Object.<string, {start: number, end: number, image: string}>} files
     * @param {string} name
     */
    this.load_file = (files, name, verbose = false) => {
        const file = files[name];
        if (file == null) {
            console.error("ERROR:", "file", name, "is not found");
            return;
        }
        const image = file.image;
        const sz = image.length / 2;

        const end = file.start + sz - 1;
        for (let i = file.start; i <= end; ++i) {
            const image_offset = i - file.start;
            const string_offset = image_offset * 2;
            const hex = file.image.slice(string_offset, string_offset + 2);
            const value = parseInt(hex, 16);
            this.write(i, value);
        }

        const size = file.end - file.start + 1;
        if (verbose) {
            console.log("*********************************");
            console.log("> file", YELLOW(name), "loaded, size", size);
        }
    };
}

function IO() {
    this.input = (port) => 0;
    this.output = (port, w8) => {};
    this.interrupt = (iff) => {};
}

console.success = false;

console.flush = function () {
    if (this.line.includes("OPERATIONAL")) {
        // TEST.COM
        console.success = true;
    }
    if (this.line.includes("complete")) {
        // 8080PRE
        console.success = true;
    }
    if (this.line.includes("CPU TESTS OK")) {
        // CPUTEST.COM
        console.success = true;
    }
    if (this.line.includes("Tests complete")) {
        // 8080EX1.COM
        console.success = true;
    }

    if (verbose) console.log("OUTPUT: " + this.line);
    this.line = "";
};

console.putchar = function (c) {
    if (c == 10) return;
    if (this.line == null) this.line = "";
    if (c == 13) this.flush();
    else this.line += String.fromCharCode(c);
};

import { preloaded_files } from "./files.js";
import { I8080 } from "./i8080.js";

function execute_test(filename, verbose = false) {
    const files = preloaded_files();

    console.success = false;

    const machine = { io: new IO() };

    const memory = new Memory(machine);
    memory.load_file(files, filename, verbose);
    machine.memory = memory;

    memory.write(5, 0xc9); // Add RET at 0x0005 to handle "CALL 5".

    const cpu = new I8080(machine);
    machine.cpu = cpu;

    cpu.jump(0x100);

    while (1) {
        // Enable this line to print out the CPU registers, the current
        // instruction and the mini-dumps addressed by the register pairs.
        // console.log(I8080_trace(cpu));

        // Enable this to be able to interrupt the execution after each
        // instruction.
        // if (!confirm(I8080_trace(cpu))) return;

        const pc = cpu.pc;
        if (memory.read(pc) == 0x76) {
            // console.log("HLT at " + pc.toString(16));
            console.flush();
            return false;
        }
        if (pc == 0x0005) {
            if (cpu.c() == 9) {
                // Print till '$'.
                for (let i = cpu.de(); memory.read(i) != 0x24; i += 1) {
                    console.putchar(memory.read(i));
                }
            }
            if (cpu.c() == 2) console.putchar(cpu.e());
        }
        cpu.instruction();
        if (cpu.pc == 0) {
            console.flush();
            if (verbose) {
                console.log("Jump to 0000 from " + pc.toString(16));
            }
            return console.success;
        }
    }
}

function main(enable_exerciser, verbose = false) {
    if (verbose) {
        console.log("Intel 8080/JS test");
        console.putchar("\n");
    }

    const tests = ["TEST.COM", "CPUTEST.COM", "8080PRE.COM"];

    if (enable_exerciser) tests.push("8080EX1.COM");

    let success = true;
    for (const test of tests) {
        if (verbose) {
            console.log("|".repeat(30));
            console.log("> RUNNING TEST", test);
        } else {
            console.log(">", test);
        }
        const result = execute_test(test, verbose);
        if (verbose) {
            console.log("|".repeat(30));
            console.log("> TEST " + test + " " + (result ? "succeed" : "FAILED"));
        }
        success &= result;
    }

    if (!success) process.exit(1);
}

const ex1 = process.argv.includes("--ex1");
const verbose = process.argv.includes("--verbose");

main(ex1, verbose);
