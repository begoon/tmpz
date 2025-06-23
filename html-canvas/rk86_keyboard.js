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

export function Keyboard() {
    this.reset = function () {
        this.state = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff];
        this.modifiers = 0xff;
    };

    this.export = () => {
        const h8 = (n) => "0x" + toHex8(n);
        return {
            state: this.state.map(h8),
            modifiers: h8(this.modifiers),
        };
    };

    this.import = (snapshot) => {
        this.state = snapshot.state.map(fromHex);
        this.modifiers = fromHex(snapshot.modifiers);
    };

    const key_table = {
        Home: [0, 0x01], // \
        End: [0, 0x02], // CTP
        F5: [0, 0x04], // AP2
        F1: [0, 0x08], // Ф1
        F2: [0, 0x10], // Ф2
        F3: [0, 0x20], // Ф3
        F4: [0, 0x40], // Ф4

        Tab: [1, 0x01], // TAB
        Delete: [1, 0x02], // ПС
        Enter: [1, 0x04], // BK
        Backspace: [1, 0x08], // ЗБ -> BS
        ArrowLeft: [1, 0x10], // <-
        ArrowUp: [1, 0x20], // UP
        ArrowRight: [1, 0x40], // ->
        ArrowDown: [1, 0x80], // DOWN

        Digit0: [2, 0x01], // 0
        Digit1: [2, 0x02], // 1
        Digit2: [2, 0x04], // 2
        Digit3: [2, 0x08], // 3
        Digit4: [2, 0x10], // 4
        Digit5: [2, 0x20], // 5
        Digit6: [2, 0x40], // 6
        Digit7: [2, 0x80], // 7

        Digit8: [3, 0x01], // 8
        Digit9: [3, 0x02], // 9
        F6: [3, 0x04], // : -> F6
        Semicolon: [3, 0x08], // ;
        Comma: [3, 0x10], // ,
        Minus: [3, 0x20], // -
        Period: [3, 0x40], // .
        Slash: [3, 0x80], // /

        F7: [4, 0x01], // @
        KeyA: [4, 0x02], // A
        KeyB: [4, 0x04], // B
        KeyC: [4, 0x08], // C
        KeyD: [4, 0x10], // D
        KeyE: [4, 0x20], // E
        KeyF: [4, 0x40], // F
        KeyG: [4, 0x80], // G

        KeyH: [5, 0x01], // H
        KeyI: [5, 0x02], // I
        KeyJ: [5, 0x04], // J
        KeyK: [5, 0x08], // K
        KeyL: [5, 0x10], // L
        KeyM: [5, 0x20], // M
        KeyN: [5, 0x40], // N
        KeyO: [5, 0x80], // O

        KeyP: [6, 0x01], // P
        KeyQ: [6, 0x02], // Q
        KeyR: [6, 0x04], // R
        KeyS: [6, 0x08], // S
        KeyT: [6, 0x10], // T
        KeyU: [6, 0x20], // U
        KeyV: [6, 0x40], // V
        KeyW: [6, 0x80], // W

        KeyX: [7, 0x01], // X
        KeyY: [7, 0x02], // Y
        KeyZ: [7, 0x04], // Z
        BracketLeft: [7, 0x08], // [
        Backslash: [7, 0x10], // \
        BracketRight: [7, 0x20], // ]
        Quote: [7, 0x40], // ^
        Space: [7, 0x80], // Space
    };

    const SS = 0x20;
    const US = 0x40;
    const RL = 0x80;

    this.keydown = (code) => {
        // console.log('keydown: %s'.format(code))
        // SHIFT
        if (code == "ShiftLeft" || code == "ShiftRight") this.modifiers &= ~SS;
        // CTRL
        if (code == "ControlLeft") this.modifiers &= ~US;
        // F10
        if (code == "F10") this.modifiers &= ~RL;
        const key = key_table[code];
        if (key) this.state[key[0]] &= ~key[1];
    };

    this.keyup = function (code) {
        // console.log('keyup: %s'.format(code))
        // SHIFT
        if (code == "ShiftLeft" || code == "ShiftRight") this.modifiers |= SS;
        // CTRL
        if (code == "ControlLeft") this.modifiers |= US;
        // F10
        if (code == "F10") this.modifiers |= RL;
        const key = key_table[code];
        if (key) this.state[key[0]] |= key[1];
    };

    this.onkeydown = (code) => {
        this.keydown(code);
    };

    this.onkeyup = (code) => {
        this.keyup(code);
    };

    this.reset();
}
