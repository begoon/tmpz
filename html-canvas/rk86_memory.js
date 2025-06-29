export class Memory {
    constructor(machine) {
        this.machine = machine;

        this.init();
        this.invalidate_access_variables();
    }

    init() {
        this.buf = new Array(0x10000).fill(0);

        this.vg75_c001_00_cmd = 0;
        this.video_screen_size_x_buf = 0;
        this.video_screen_size_y_buf = 0;
        this.ik57_e008_80_cmd = 0;
        this.vg75_c001_80_cmd = 0;
        this.cursor_x_buf = 0;
        this.cursor_y_buf = 0;
        this.vg75_c001_60_cmd = 0;
        this.tape_8002_as_output = 0;
        this.video_memory_base_buf = 0;
        this.video_memory_size_buf = 0;
        this.video_memory_base = 0;
        this.video_memory_size = 0;
        this.video_screen_size_x = 0;
        this.video_screen_size_y = 0;
        this.video_screen_cursor_x = 0;
        this.video_screen_cursor_y = 0;
    }

    zero_ram() {
        for (let i = 0; i < 0x8000; ++i) this.buf[i] = 0;
    }

    invalidate_access_variables() {
        this.last_access_address = 0;
        this.last_access_operation = undefined;
    }

    length() {
        return 0x10000;
    }

    read_raw(addr) {
        return this.buf[addr & 0xffff] & 0xff;
    }

    read(addr) {
        addr &= 0xffff;
        this.last_access_address = addr;
        this.last_access_operation = "read";

        if (addr === 0x8002) return this.machine.keyboard.modifiers;

        if (addr === 0x8001) {
            const keyboard_state = this.machine.keyboard.state;
            let ch = 0xff;
            const kbd_scanline = ~this.buf[0x8000];
            for (let i = 0; i < 8; i++) if ((1 << i) & kbd_scanline) ch &= keyboard_state[i];
            return ch;
        }

        if (addr === 0xc001) {
            return 0x20 | (this.machine.screen.light_pen_active ? 0x10 : 0x00);
        }

        if (addr === 0xc000) {
            if (this.vg75_c001_60_cmd === 1) {
                this.vg75_c001_60_cmd = 2;
                return this.machine.screen.light_pen_x;
            }
            if (this.vg75_c001_60_cmd === 2) {
                this.vg75_c001_60_cmd = 0;
                return this.machine.screen.light_pen_y;
            }
            return 0x00;
        }

        return this.buf[addr];
    }

    write_raw(addr, byte) {
        this.buf[addr & 0xffff] = byte & 0xff;
    }

    write = (addr, byte) => {
        addr &= 0xffff;
        byte &= 0xff;

        this.last_access_address = addr;
        this.last_access_operation = "write";

        if (addr >= 0xf800) return;
        this.buf[addr] = byte;

        const peripheral_reg = addr & 0xefff;

        if (peripheral_reg === 0x8003) {
            if (byte & 0x80) {
                // Mode set
            } else {
                const bit = (byte >> 1) & 0x03;
                const value = byte & 0x01;
                if (bit === 3) this.set_ruslat(value);
            }
            return;
        }

        if (peripheral_reg === 0xc001 && byte === 0x27) return;
        if (peripheral_reg === 0xc001 && byte === 0xe0) return;

        if (peripheral_reg === 0xc001 && byte === 0x80) {
            this.vg75_c001_80_cmd = 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_80_cmd === 1) {
            this.vg75_c001_80_cmd += 1;
            this.cursor_x_buf = byte + 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_80_cmd === 2) {
            this.cursor_y_buf = byte + 1;
            this.machine.screen.set_cursor(this.cursor_x_buf - 1, this.cursor_y_buf - 1);
            this.video_screen_cursor_x = this.cursor_x_buf;
            this.video_screen_cursor_y = this.cursor_y_buf;
            this.vg75_c001_80_cmd = 0;
            return;
        }

        if (peripheral_reg === 0xc001 && byte === 0x60) {
            if (this.machine.screen.light_pen_active) this.vg75_c001_60_cmd = 1;
            return;
        }

        if (peripheral_reg === 0xc001 && byte === 0x00) {
            this.vg75_c001_00_cmd = 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_00_cmd === 1) {
            this.video_screen_size_x_buf = (byte & 0x7f) + 1;
            this.vg75_c001_00_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_00_cmd === 2) {
            this.video_screen_size_y_buf = (byte & 0x3f) + 1;
            this.vg75_c001_00_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_00_cmd === 3) {
            this.vg75_c001_00_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xc000 && this.vg75_c001_00_cmd === 4) {
            this.vg75_c001_00_cmd = 0;
            if (this.video_screen_size_x_buf && this.video_screen_size_y_buf) {
                this.video_screen_size_x = this.video_screen_size_x_buf;
                this.video_screen_size_y = this.video_screen_size_y_buf;
                this.machine.screen.set_geometry(this.video_screen_size_x, this.video_screen_size_y);
            }
            return;
        }

        if (peripheral_reg === 0xe008 && byte === 0x80) {
            this.ik57_e008_80_cmd = 1;
            this.tape_8002_as_output = 1;
            return;
        }

        if (peripheral_reg === 0xe004 && this.ik57_e008_80_cmd === 1) {
            this.video_memory_base_buf = byte;
            this.ik57_e008_80_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xe004 && this.ik57_e008_80_cmd === 2) {
            this.video_memory_base_buf |= byte << 8;
            this.ik57_e008_80_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xe005 && this.ik57_e008_80_cmd === 3) {
            this.video_memory_size_buf = byte;
            this.ik57_e008_80_cmd += 1;
            return;
        }

        if (peripheral_reg === 0xe005 && this.ik57_e008_80_cmd === 4) {
            this.video_memory_size_buf = ((this.video_memory_size_buf | (byte << 8)) & 0x3fff) + 1;
            this.ik57_e008_80_cmd = 0;
            this.video_memory_base = this.video_memory_base_buf;
            this.video_memory_size = this.video_memory_size_buf;
            this.machine.screen.set_video_memory(this.video_memory_base, this.video_memory_size);
            return;
        }

        if (peripheral_reg === 0xe008 && byte === 0xa4) {
            this.tape_8002_as_output = 0;
            return;
        }

        if (addr === 0x8002) {
            if (this.tape_8002_as_output) {
                this.tape_write_bit(byte & 0x01);
            }
            return;
        }
    };

    tape_write_bit(bit) {
        this.machine.tape.write_bit(bit);
    }

    set_ruslat(value) {
        if (this.update_ruslat) this.update_ruslat(value);
    }

    load_file(file) {
        for (let i = file.start; i <= file.end; ++i) {
            this.write_raw(i, file.image[i - file.start]);
        }
    }
}
