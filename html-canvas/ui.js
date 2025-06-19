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

export function UI(machine) {
    this.machine = machine;

    this.canvas = document.getElementById("canvas");

    if (!this.canvas.getContext) {
        alert("Tag <canvas> is not support is the browser");
        return;
    }

    this.resize_canvas = function (width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
    };

    this.fullscreen = () => canvas.requestFullScreen();

    this.reset = function () {
        this.machine.memory.keyboard.reset();
        this.machine.cpu.jump(0xf800);
        console.log("Reset");
    };

    this.restart = function () {
        this.machine.memory.zero_ram();
        this.reset();
    };

    this.ruslat = document.getElementById("ruslat");
    this.ruslat_state = false;

    this.update_ruslat = (value) => {
        if (value === this.ruslat_state) return;
        this.ruslat_state = value;
        this.ruslat.innerHTML = value ? "РУС" : "ЛАТ";
    };

    this.ruslat.addEventListener("click", () => {
        // Конкретный адрес флага раскладки оригинального монитора 32КБ.
        const ruslat_flag = 0x7606;
        const state = this.machine.memory.read(ruslat_flag) ? 0x00 : 0xff;
        this.machine.memory.write(ruslat_flag, state);
        this.machine.update_ruslat(state);
    });

    this.sound = document.getElementById("sound");
    this.sound.addEventListener("click", () => {
        this.machine.runner.init_sound(sound.checked);
        console.log("Sound " + (this.machine.runner.sound ? "enabled" : "disabled"));
    });

    this.ips = document.getElementById("ips");
    this.tps = document.getElementById("tps");

    this.update_perf = () => {
        function update(element, value) {
            element.innerHTML = Math.floor(value * 1000).toLocaleString();
        }
        update(ips, this.machine.runner.instructions_per_millisecond);
        update(tps, this.machine.runner.ticks_per_millisecond);
    };
    setInterval(this.update_perf, 2000);
}
