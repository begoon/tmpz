import { Bus } from "./bus.js";
import { I8080 } from "./i8080.js";
import { i8080disasm } from "./i8080disasm_panel.js";
import FileParser from "./rk86_file_parser.js";
import { rk86_font_image } from "./rk86_font.js";
import { Keyboard } from "./rk86_keyboard.js";
import { Memory } from "./rk86_memory.js";
import { Runner } from "./rk86_runner.js";
import { Screen } from "./rk86_screen.js";
import { Tape } from "./rk86_tape.js";
import { tape_catalog } from "./tape_catalog.js";
import { UI } from "./ui.js";

function IO() {
    this.input = function (port) {
        return 0;
    };
    this.output = function (port, w8) {};
    this.interrupt = function (iff) {};
}

export async function main() {
    const bus = new Bus();

    bus.on("sound", (enabled) => console.log("sound enabled:", enabled));

    const keyboard = new Keyboard();
    const io = new IO();

    const machine = {
        bus,
        font: rk86_font_image(),
        file_parser: new FileParser(),
        //
        keyboard,
        io,
    };
    machine.memory = new Memory(machine);

    machine.ui = new UI(machine);
    machine.screen = new Screen(machine);
    machine.cpu = new I8080(machine);
    machine.runner = new Runner(machine);

    machine.tape = new Tape(machine);

    async function load_file(name) {
        const array = Array.from(new Uint8Array(await (await fetch("./files/" + name)).arrayBuffer()));
        console.log(`loading file: ${name}, size: ${array.length} bytes`);
        return machine.file_parser.parse_rk86_binary(name, array);
    }

    machine.memory.load_file(await load_file("mon32.bin"));
    // machine.memory.load_file(await load_file("DIVERSE.GAM"));
    machine.memory.load_file(await load_file("GFIRE.GAM"));
    // machine.memory.load_file(await load_file("RESCUE.GAM"));

    machine.runner.execute();

    bus.on("reset", () => reset());

    function reset() {
        machine.keyboard.reset();
        machine.cpu.jump(0xf800);
    }

    document.getElementById("reset").addEventListener("click", () => {
        bus.emit("reset");
    });

    document.getElementById("restart").addEventListener("click", () => {
        machine.memory.zero_ram();
        bus.emit("reset");
    });

    const header = document.getElementById("header");
    const footer = document.getElementById("footer");
    const disassember_panel = document.getElementById("disassembler_panel");
    document.addEventListener("fullscreenchange", () => {
        const fullscreen = document.fullscreenElement;
        if (!fullscreen) {
            header.classList.remove("hidden");
            footer.classList.remove("hidden");
            disassember_panel.classList.remove("hidden");
        } else {
            header.classList.add("hidden");
            footer.classList.add("hidden");
            disassember_panel.classList.add("hidden");
        }
    });

    machine.memory.update_ruslat = machine.ui.update_ruslat;

    const file_selector = document.getElementById("file_selector");
    for (const name of tape_catalog()) {
        file_selector.add(new Option(name, name), null);
    }

    document.getElementById("load").addEventListener("click", async () => {
        const filename = file_selector.options[file_selector.selectedIndex].value;
        console.log(`loading file: ${filename}`);
        const file = await load_file(filename);
        console.log(`loaded file: ${filename}`);
        machine.memory.load_file(file);
        alert(
            `` +
                `Загружен файл "${filename}"\n` +
                `Адрес: 0x${file.start.toString(16).padStart(4, "0")}` +
                `-` +
                `0x${file.end.toString(16).padStart(4, "0")}\n` +
                `Запуск: G${file.entry.toString(16)}`
        );
    });

    document.getElementById("run").addEventListener("click", async () => {
        const filename = file_selector.options[file_selector.selectedIndex].value;
        console.log(`loading file: ${filename}`);
        const file = await load_file(filename);
        console.log(`loaded file: ${filename}`);
        machine.memory.load_file(file);
        machine.cpu.jump(file.entry);
    });

    i8080disasm.refresh(machine.memory);
    machine.ui.i8080disasm = i8080disasm;
    window.i8080disasm = i8080disasm;

    machine.ui.start_update_perf();
}

await main();
