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

export function Screen(machine) {
    this.machine = machine;

    const update_rate = 25;
    const cursor_rate = 500;

    const char_width = 6;
    const char_height = 8;
    const char_height_gap = 2;

    const cursor_width = char_width;
    const cursor_height = 1;
    const cursor_offset_white = 27;

    this.scale_x = 1;
    this.scale_y = 1;

    this.width = 78;
    this.height = 30;

    this.cursor_state = true;
    this.cursor_x = 0;
    this.cursor_y = 0;

    this.video_memory_base = 0;
    this.video_memory_size = 0;

    this.cache = [];

    this.font = new Image();
    this.font.src = this.machine.font; // -> "rk86_font.bmp";

    this.light_pen_x = 0;
    this.light_pen_y = 0;
    this.light_pen_active = 0;

    this.init_cache = (sz) => {
        for (let i = 0; i < sz; ++i) this.cache[i] = true;
    };

    this.draw_char = (x, y, ch) => {
        this.ctx.drawImage(
            this.font,
            2,
            char_height * ch,
            char_width,
            char_height,
            x * char_width * this.scale_x,
            y * (char_height + char_height_gap) * this.scale_y,
            char_width * this.scale_x,
            char_height * this.scale_y
        );
    };

    this.draw_cursor = (x, y, visible) => {
        this.ctx.drawImage(
            this.font,
            2,
            cursor_offset_white + (visible ? 0 : 1),
            char_width,
            1,
            x * char_width * this.scale_x,
            (y * (char_height + char_height_gap) + char_height) * this.scale_y,
            char_width * this.scale_x,
            1 * this.scale_y
        );
    };

    this.flip_cursor = () => {
        this.draw_cursor(this.cursor_x, this.cursor_y, this.cursor_state);
        this.cursor_state = !this.cursor_state;
        setTimeout(() => this.flip_cursor(), cursor_rate);
    };

    this.init = () => {
        this.ctx = this.machine.ui.canvas.getContext("2d");
    };

    this.disable_smoothing = () => {
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.imageSmoothingEnabled = false;
    };

    this.set_geometry = function (width, height) {
        this.width = width;
        this.height = height;
        this.video_memory_size = width * height;

        this.machine.ui.update_screen_geometry(this.width, this.height);
        console.log(`screen geometry: ${width} x ${height}`);

        const canvas_width = this.width * char_width * this.scale_x;
        const canvas_height = this.height * (char_height + char_height_gap) * this.scale_y;
        this.machine.ui.resize_canvas(canvas_width, canvas_height);

        this.disable_smoothing();
        this.ctx.fillRect(0, 0, canvas_width, canvas_height);
    };

    this.last_video_memory_base = -1;
    this.last_video_memory_size = -1;

    this.set_video_memory = function (base) {
        this.video_memory_base = base;
        this.init_cache(this.video_memory_size);

        this.machine.ui.update_video_memory_base(this.video_memory_base);

        if (
            this.last_video_memory_base !== this.video_memory_base ||
            this.last_video_memory_size !== this.video_memory_size
        ) {
            console.log(`video memory:`, `${this.video_memory_base.toString(16)}`, `size: ${this.video_memory_size}`);
            this.last_video_memory_base = this.video_memory_base;
            this.last_video_memory_size = this.video_memory_size;
        }
    };

    this.set_cursor = function (x, y) {
        this.draw_cursor(this.cursor_x, this.cursor_y, false);
        this.cursor_x = x;
        this.cursor_y = y;
    };

    this.draw_screen = () => {
        const memory = this.machine.memory;
        let i = this.video_memory_base;
        for (let y = 0; y < this.height; ++y) {
            for (let x = 0; x < this.width; ++x) {
                const cache_i = i - this.video_memory_base;
                const ch = memory.read(i);
                if (this.cache[cache_i] != ch) {
                    this.draw_char(x, y, ch);
                    this.cache[cache_i] = ch;
                }
                i += 1;
            }
        }
        setTimeout(() => this.draw_screen(), update_rate);
    };

    this.init();

    this.flip_cursor();
    this.draw_screen();

    this.machine.ui.canvas.onmousemove = (event) => {
        const canvas = this.machine.ui.canvas;
        const x = Math.floor((event.x + 1 - canvas.offsetLeft) / (char_width * this.scale_x));
        const y = Math.floor((event.y + 1 - canvas.offsetTop) / ((char_height + char_height_gap) * this.scale_y));
        this.light_pen_x = x;
        this.light_pen_y = y;
    };

    this.machine.ui.canvas.onmouseup = (event) => {
        this.light_pen_active = 0;
    };

    this.machine.ui.canvas.onmousedown = (event) => {
        this.light_pen_active = 1;
    };
}
