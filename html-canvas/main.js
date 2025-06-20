// Part of Radio-86RK in JavaScript based on I8080/JS
//
// Copyright (C) 2012 Alexander Demin <alexander@demin.ws>
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2, or (at your option)
// any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import { I8080 } from "./i8080.js";
import FileParser from "./rk86_file_parser.js";
import { rk86_font_image } from "./rk86_font.js";
import { Keyboard } from "./rk86_keyboard.js";
import { Memory } from "./rk86_memory.js";
import { Runner } from "./rk86_runner.js";
import { Screen } from "./rk86_screen.js";
import { UI } from "./ui.js";

function IO() {
    this.input = function (port) {
        return 0;
    };
    this.output = function (port, w8) {};
    this.interrupt = function (iff) {};
}

export async function main() {
    const machine = {
        font: rk86_font_image(),
        file_parser: new FileParser(),
        //
        keyboard: new Keyboard(),
        io: new IO(),
    };
    machine.memory = new Memory(machine);
    machine.ui = new UI(machine);
    machine.screen = new Screen(machine);
    machine.cpu = new I8080(machine);
    machine.runner = new Runner(machine);

    async function load_file(name) {
        const array = Array.from(new Uint8Array(await (await fetch("./files/" + name)).arrayBuffer()));
        return machine.file_parser.parse_rk86_binary(name, array);
    }

    machine.memory.load_file(await load_file("mon32.bin"));
    // machine.memory.load_file(await load_file("DIVERSE.GAM"));
    // machine.memory.load_file(await load_file("GFIRE.GAM"));
    machine.memory.load_file(await load_file("RESCUE.GAM"));

    machine.runner.execute();

    function reset() {
        machine.keyboard.reset();
        machine.cpu.jump(0xf800);
    }

    document.getElementById("reset").addEventListener("click", () => {
        reset();
        console.log("Reset");
    });

    document.getElementById("restart").addEventListener("click", () => {
        machine.memory.zero_ram();
        reset();
        console.log("Restart");
    });

    document.getElementById("pause").addEventListener("click", () => {
        machine.runner.paused = !machine.runner.paused;
        document.getElementById("pause").textContent = machine.runner.paused ? "Resume" : "Pause";
        document.getElementById("pause").classList.toggle("paused", machine.runner.paused);
        console.log(machine.runner.paused ? "Paused" : "Resumed");
    });

    document.getElementById("fullscreen").addEventListener("click", () => {
        machine.ui.canvas.requestFullscreen();
    });

    const header = document.getElementById("header");
    const footer = document.getElementById("footer");
    document.addEventListener("fullscreenchange", () => {
        const fullscreen = document.fullscreenElement;
        if (!fullscreen) {
            console.log("exit fullscreen");
            header.classList.remove("hidden");
            footer.classList.remove("hidden");
        } else {
            console.log("enter fullscreen");
            header.classList.add("hidden");
            footer.classList.add("hidden");
        }
    });

    document.getElementById("ruslat").addEventListener("click", () => {
        machine.ui.update_ruslat = !machine.ui.update_ruslat;
        document.getElementById("ruslat").textContent = machine.ui.update_ruslat ? "RU" : "LAT";
    });
    machine.memory.update_ruslat = machine.ui.update_ruslat;
}

await main();
