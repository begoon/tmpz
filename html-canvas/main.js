import { I8080 } from "./i8080.js";
import FileParser from "./rk86_file_parser.js";
import { rk86_font_image } from "./rk86_font.js";
import { Keyboard } from "./rk86_keyboard.js";
import { Memory } from "./rk86_memory.js";
import { Runner } from "./rk86_runner.js";
import { Screen } from "./rk86_screen.js";
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
    const keyboard = new Keyboard();
    const io = new IO();

    const machine = {
        font: rk86_font_image(),
        file_parser: new FileParser(),
        //
        keyboard,
        io,
    };
    machine.memory = new Memory(keyboard);
    machine.ui = new UI(machine);
    machine.screen = new Screen(machine);
    machine.memory.attach_screen(machine.screen);
    machine.cpu = new I8080(machine);
    machine.runner = new Runner(machine);

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

    function reset() {
        machine.keyboard.reset();
        machine.cpu.jump(0xf800);
    }

    document.getElementById("reset").addEventListener("click", () => {
        reset();
    });

    document.getElementById("restart").addEventListener("click", () => {
        machine.memory.zero_ram();
        reset();
    });

    const pause = document.getElementById("pause");
    pause.addEventListener("click", () => {
        machine.runner.paused = !machine.runner.paused;
        const icon = document.getElementById("pause-icon");
        console.log(icon);
        icon.src = machine.runner.paused ? icon.dataset.on : icon.dataset.off;
    });

    document.getElementById("fullscreen").addEventListener("click", () => {
        machine.ui.canvas.requestFullscreen();
    });

    const header = document.getElementById("header");
    const footer = document.getElementById("footer");
    document.addEventListener("fullscreenchange", () => {
        const fullscreen = document.fullscreenElement;
        if (!fullscreen) {
            header.classList.remove("hidden");
            footer.classList.remove("hidden");
        } else {
            header.classList.add("hidden");
            footer.classList.add("hidden");
        }
    });

    machine.memory.update_ruslat = machine.ui.update_ruslat;

    const file_selector = document.getElementById("file_selector");
    for (const name of tape_catalog()) {
        file_selector.add(new Option(name, name), null);
    }

    document.getElementById("load").addEventListener("click", async () => {
        const file_selector = document.getElementById("file_selector");
        const filename = file_selector.options[file_selector.selectedIndex].value;
        console.log(`loading file: ${filename}`);
        const file = await load_file(filename);
        console.log(`loaded file: ${filename}`);
        machine.memory.load_file(file);
    });

    document.getElementById("run").addEventListener("click", async () => {
        const file_selector = document.getElementById("file_selector");
        const filename = file_selector.options[file_selector.selectedIndex].value;
        console.log(`loading file: ${filename}`);
        const file = await load_file(filename);
        console.log(`loaded file: ${filename}`);
        machine.memory.load_file(file);
        machine.cpu.jump(file.entry);
    });
}

await main();
