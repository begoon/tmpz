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

import { rk86_font_image } from "./rk86_font.js";
import { Memory } from "./rk86_memory.js";
import { Screen } from "./rk86_screen.js";
import { UI } from "./ui.js";

export function main() {
    const memory = new Memory();

    for (let i = 0; i < 78 * 30; i++)
        memory.write_raw(i, Math.floor(Math.random() * 0x80));

    let x = 0;
    let y = 0;
    let ch = undefined;
    setInterval(() => {
        if (ch !== undefined) memory.write_raw(y * 78 + x, ch);
        x += 1;
        if (x >= 78) (x = 0), (y += 1);
        if (y >= 30) y = 0;
        ch = memory.read_raw(y * 78 + x);
        screen.set_cursor(x, y);
        memory.write_raw(y * 78 + x, 0x20);
        console.log(`Cursor at (${x}, ${y}), char: ${ch}`);
    }, 100);

    const ui = new UI(memory);

    screen = new Screen(rk86_font_image(), ui, memory);
    screen.set_geometry(78, 30);
    screen.set_video_memory(0);

    ui.canvas.addEventListener("click", () => {
        ui.canvas.requestFullscreen();
    });
}

main();
