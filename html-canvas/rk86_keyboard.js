export class Keyboard {
    constructor() {
        this.reset();
    }

    reset() {
        this.state = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff];
        this.modifiers = 0xff;
    }

    export() {
        const h8 = (n) => "0x" + toHex8(n);
        return {
            state: this.state.map(h8),
            modifiers: h8(this.modifiers),
        };
    }

    import(snapshot) {
        this.state = snapshot.state.map(fromHex);
        this.modifiers = fromHex(snapshot.modifiers);
    }

    keydown(code) {
        // SHIFT
        if (code === "ShiftLeft" || code === "ShiftRight") this.modifiers &= ~SS;
        // CTRL
        if (code === "ControlLeft") this.modifiers &= ~US;
        // F10
        if (code === "F10") this.modifiers &= ~RL;
        const key = Keyboard.key_table[code];
        if (key) this.state[key[0]] &= ~key[1];
    }

    keyup(code) {
        // SHIFT
        if (code === "ShiftLeft" || code === "ShiftRight") this.modifiers |= SS;
        // CTRL
        if (code === "ControlLeft") this.modifiers |= US;
        // F10
        if (code === "F10") this.modifiers |= RL;
        const key = Keyboard.key_table[code];
        if (key) this.state[key[0]] |= key[1];
    }

    onkeydown(code) {
        this.keydown(code);
    }

    onkeyup(code) {
        this.keyup(code);
    }

    static key_table = {
        Home: [0, 0x01],
        End: [0, 0x02],
        F5: [0, 0x04],
        F1: [0, 0x08],
        F2: [0, 0x10],
        F3: [0, 0x20],
        F4: [0, 0x40],
        Tab: [1, 0x01],
        Delete: [1, 0x02],
        Enter: [1, 0x04],
        Backspace: [1, 0x08],
        ArrowLeft: [1, 0x10],
        ArrowUp: [1, 0x20],
        ArrowRight: [1, 0x40],
        ArrowDown: [1, 0x80],
        Digit0: [2, 0x01],
        Digit1: [2, 0x02],
        Digit2: [2, 0x04],
        Digit3: [2, 0x08],
        Digit4: [2, 0x10],
        Digit5: [2, 0x20],
        Digit6: [2, 0x40],
        Digit7: [2, 0x80],
        Digit8: [3, 0x01],
        Digit9: [3, 0x02],
        F6: [3, 0x04],
        Semicolon: [3, 0x08],
        Comma: [3, 0x10],
        Minus: [3, 0x20],
        Period: [3, 0x40],
        Slash: [3, 0x80],
        F7: [4, 0x01],
        KeyA: [4, 0x02],
        KeyB: [4, 0x04],
        KeyC: [4, 0x08],
        KeyD: [4, 0x10],
        KeyE: [4, 0x20],
        KeyF: [4, 0x40],
        KeyG: [4, 0x80],
        KeyH: [5, 0x01],
        KeyI: [5, 0x02],
        KeyJ: [5, 0x04],
        KeyK: [5, 0x08],
        KeyL: [5, 0x10],
        KeyM: [5, 0x20],
        KeyN: [5, 0x40],
        KeyO: [5, 0x80],
        KeyP: [6, 0x01],
        KeyQ: [6, 0x02],
        KeyR: [6, 0x04],
        KeyS: [6, 0x08],
        KeyT: [6, 0x10],
        KeyU: [6, 0x20],
        KeyV: [6, 0x40],
        KeyW: [6, 0x80],
        KeyX: [7, 0x01],
        KeyY: [7, 0x02],
        KeyZ: [7, 0x04],
        BracketLeft: [7, 0x08],
        Backslash: [7, 0x10],
        BracketRight: [7, 0x20],
        Quote: [7, 0x40],
        Space: [7, 0x80],
    };
}

const SS = 0x20;
const US = 0x40;
const RL = 0x80;
