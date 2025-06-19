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

import { Sound } from "./rk86_sound.js";

export function Runner(machine) {
    this.machine = machine;

    this.paused = false;
    this.tracer = null;
    this.visualizer = null;

    this.last_instructions = [];

    this.previous_batch_time = 0;

    this.total_ticks = 0;

    this.last_iff_raise_ticks = 0;
    this.last_iff = 0;
    this.sound = false;

    const FREQ = 1780000;
    const TICK_PER_MS = FREQ / 100;

    this.interrupt = (iff) => {
        if (!this.sound) return;
        if (this.last_iff == iff) return;
        if (this.last_iff == 0 && iff == 1) {
            this.last_iff_raise_ticks = this.total_ticks;
        }
        if (this.last_iff == 1 && iff == 0) {
            const tone_ticks = this.total_ticks - this.last_iff_raise_ticks;
            const tone = FREQ / (tone_ticks * 2);
            const duration = 1 / tone;
            this.sound.play(tone, duration);
        }
        this.last_iff = iff;
    };

    this.init_sound = (enabled) => (this.sound = enabled ? new Sound() : false);

    this.machine.io.interrupt = this.interrupt;
    this.machine.cpu.jump(0xf800);

    this.execute = function () {
        clearTimeout(this.execute_timer);
        if (!this.paused) {
            let batch_ticks = 0;
            let batch_instructions = 0;
            while (batch_ticks < TICK_PER_MS) {
                if (this.tracer) {
                    this.tracer("before");
                    if (this.paused) break;
                }
                this.last_instructions.push(machine.cpu.pc);
                if (this.last_instructions.length > 5) {
                    this.last_instructions.shift();
                }
                this.machine.cpu.memory.invalidate_access_variables();
                const instruction_ticks = this.machine.cpu.instruction();
                batch_ticks += instruction_ticks;
                this.total_ticks += instruction_ticks;

                if (this.tracer) {
                    this.tracer("after");
                    if (this.paused) break;
                }
                if (this.visualizer) {
                    this.visualizer.hit(this.cpu.memory.read_raw(this.cpu.pc));
                }
                batch_instructions += 1;
            }
            const now = +new Date();
            const elapsed = now - this.previous_batch_time;
            this.previous_batch_time = now;

            this.instructions_per_millisecond = batch_instructions / elapsed;
            this.ticks_per_millisecond = batch_ticks / elapsed;
        }
        this.execute_timer = window.setTimeout(() => this.execute(), 10);
    };

    this.pause = function () {
        this.paused = true;
    };

    this.resume = function () {
        this.paused = false;
    };
}
