export class UI {
    constructor(machine) {
        this.machine = machine;

        this.canvas = document.getElementById("canvas");
        if (!this.canvas || !this.canvas.getContext) {
            alert("Tag <canvas> is not supported in the browser");
            return;
        }

        this.ruslat = document.getElementById("ruslat");
        this.ruslat_state = false;

        this.sound = document.getElementById("sound");
        this.sound_enabled = false;

        this.ips = document.getElementById("ips");
        this.tps = document.getElementById("tps");

        this.meta_press_count = 0;

        this.command_mode = false;

        this.configureEventListeners();
    }

    start_update_perf = () => setInterval(() => this.update_perf(), 2000);

    resize_canvas(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
    }

    fullscreen() {
        this.canvas.requestFullscreen();
    }

    reset() {
        this.machine.keyboard.reset();
        this.machine.cpu.jump(0xf800);
        console.log("Reset");
    }

    restart() {
        this.machine.memory.zero_ram();
        this.reset();
    }

    update_ruslat = (value) => {
        if (value === this.ruslat_state) return;
        this.ruslat_state = value;
        this.ruslat.textContent = value ? "РУС" : "ЛАТ";
    };

    update_perf() {
        const update = (element, value) => {
            element.innerHTML = Math.floor(value * 1000).toLocaleString();
        };
        update(this.ips, this.machine.runner.instructions_per_millisecond);
        update(this.tps, this.machine.runner.ticks_per_millisecond);
    }

    update_video_memory_base(base) {
        document.getElementById("video-base").textContent = base.toString(16).toUpperCase();
    }

    update_screen_geometry(width, height) {
        document.getElementById("video-width").textContent = width.toString();
        document.getElementById("video-height").textContent = height.toString();
    }

    toggle_disassembler() {
        this.disassembler_visible = !this.disassembler_visible;
        this.disassembler_panel.style.display = this.disassembler_visible ? "block" : "none";
        this.disassembler_icon.src = "i/disassembler-" + (this.disassembler_visible ? "on" : "off") + ".svg";
        this.machine.ui.i8080disasm.refresh();
        this.machine.ui.i8080disasm.go_code(this.machine.cpu.pc);
    }

    configureEventListeners() {
        const machine = this.machine;

        document.getElementById("ruslat-toggle").addEventListener("click", () => {
            const ruslat_flag = 0x7606;
            const state = this.machine.memory.read(ruslat_flag) ? 0x00 : 0xff;
            this.machine.memory.write(ruslat_flag, state);
            this.update_ruslat(state);
        });

        this.sound.addEventListener("click", () => {
            this.sound_enabled = !this.sound_enabled;
            this.machine.runner.init_sound(this.sound_enabled);
            console.log("sound " + (this.sound_enabled ? "enabled" : "disabled"));

            const toggle = document.getElementById("sound-icon-toggle");
            toggle.src = this.sound_enabled ? toggle.dataset.on : toggle.dataset.muted;

            const icon = document.getElementById("sound-icon");
            icon.textContent = icon.dataset[this.sound_enabled ? "on" : "off"];
            icon.classList.add("visible");
            setTimeout(() => icon.classList.remove("visible"), 2000);
        });

        this.disassembler_panel = document.getElementById("disassembler_panel");
        this.disassembler_icon = document.getElementById("disassembler_icon");
        this.disassembler_visible = false;

        document.getElementById("disassembler_toggle").addEventListener("click", () => {
            this.toggle_disassembler();
        });

        this.disassemblerOffsetX = 0;
        this.disassemblerOffsetY = 0;
        this.disassemberIsDragging = false;

        disassembler_panel.addEventListener("mousedown", (e) => {
            this.disassemberIsDragging = true;
            this.disassemblerOffsetX = e.clientX - this.disassembler_panel.offsetLeft;
            this.disassemblerOffsetY = e.clientY - this.disassembler_panel.offsetTop;
        });

        disassembler_panel.addEventListener("mousemove", (e) => {
            if (this.disassemberIsDragging) {
                const left = e.clientX - this.disassemblerOffsetX;
                const top = e.clientY - this.disassemblerOffsetY;

                const width = document.documentElement.clientWidth;
                const height = document.documentElement.clientHeight;

                if (left < 0 || left + this.disassembler_panel.offsetWidth > width - 1) {
                    return;
                }
                if (top < 0 || top + this.disassembler_panel.offsetHeight > height - 1) {
                    return;
                }
                this.disassembler_panel.style.left = left + "px";
                this.disassembler_panel.style.top = top + "px";
            }
        });

        disassembler_panel.addEventListener("mouseup", () => {
            this.disassemberIsDragging = false;
        });

        document.onkeydown = (event) => {
            if (this.command_mode) {
                switch (event.code) {
                    case "KeyD":
                        this.toggle_disassembler();
                        this.disassembler_panel.focus();
                        break;
                    case "KeyS":
                        this.sound.click();
                        break;
                    case "KeyR":
                        this.restart();
                        break;
                    case "KeyF":
                        this.fullscreen();
                        break;
                }
                this.command_mode = false;
                document.getElementById("shortcuts").classList.remove("visible");
                return;
            }

            if (this.meta_press_count > 0) {
                if (event.code === "KeyK") {
                    this.command_mode = true;
                    document.getElementById("shortcuts").classList.add("visible");
                }
                return;
            }

            if (event.key === "Meta") {
                this.meta_press_count += 1;
                return;
            }

            this.machine.keyboard.onkeydown(event.code);
            return false;
        };

        document.onkeyup = (event) => {
            if (event.key === "Meta") {
                if (this.meta_press_count > 0) this.meta_press_count -= 1;
                return;
            }
            if (this.meta_press_count > 0) return;

            this.machine.keyboard.onkeyup(event.code);
            return false;
        };

        this.disassembler_panel.addEventListener("keyup", (event) => {
            if (event.key === "Escape") {
                this.disassembler_panel.blur();
                this.toggle_disassembler();
            }
            if (event.key === "Enter") {
                this.machine.ui.i8080disasm.form_go_code();
            }
            event.stopPropagation();
        });

        this.disassembler_panel.addEventListener("keydown", (event) => {
            event.stopPropagation();
        });

        document.getElementById("fullscreen").addEventListener("click", () => {
            this.machine.ui.canvas.requestFullscreen();
        });

        const pause = document.getElementById("pause");
        pause.addEventListener("click", () => {
            machine.runner.paused = !machine.runner.paused;
            const icon = document.getElementById("pause-icon");
            icon.src = machine.runner.paused ? icon.dataset.on : icon.dataset.off;
            this.machine.ui.i8080disasm.go_code(machine.cpu.pc);
        });

        // disassembler

        document.getElementById("disasm_form_code_shift_back_page").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_code_shift(false, -1);
        });
        document.getElementById("disasm_form_code_shift_back_one").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_code_shift(true, -1);
        });
        document.getElementById("disasm_form_go_code").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_go_code();
        });
        document.getElementById("disasm_form_code_shift_forward_one").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_code_shift(true, 1);
        });
        document.getElementById("disasm_form_code_shift_forward_page").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_code_shift(false, 1);
        });

        document.getElementById("disasm_form_data_shift_back_one").addEventListener("click", () => {
            this.machine.ui.i8080disasm.go_data_shift(-1, { one: true });
        });
        document.getElementById("disasm_form_data_shift_back_page").addEventListener("click", () => {
            this.machine.ui.i8080disasm.go_data_shift(-1);
        });
        document.getElementById("disasm_form_go_data").addEventListener("click", () => {
            this.machine.ui.i8080disasm.form_go_data();
        });
        document.getElementById("disasm_form_data_shift_forward_page").addEventListener("click", () => {
            this.machine.ui.i8080disasm.go_data_shift(1);
        });
        document.getElementById("disasm_form_data_shift_forward_one").addEventListener("click", () => {
            this.machine.ui.i8080disasm.go_data_shift(1, { one: true });
        });
    }

    update_activity_indicator = (active) => {
        document.getElementById("tape_activity_indicator").style.visibility = active ? "visible" : "hidden";
    };

    update_written_bytes = (count) => {
        document.getElementById("tape_written_bytes").textContent = count.toString().padStart(4, "0");
        if (count === 1) this.hightlight_written_bytes(true);
        else if (count === 0) this.hightlight_written_bytes(false);
    };

    hightlight_written_bytes = (on) => {
        document.getElementById("tape_written_bytes").classList.toggle("tape_active", on);
        document.getElementById("tape_activity_indicator").src = on ? "i/tape-data.svg" : "i/tape-preamble.svg";
    };
}
