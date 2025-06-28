export class UI {
    constructor(machine) {
        this.machine = machine;

        this.canvas = document.getElementById("canvas");
        if (!this.canvas || !this.canvas.getContext) {
            alert("Tag <canvas> is not supported in the browser");
            return;
        }

        this.ruslat = document.getElementById("ruslat");
        console.log("ruslat", this.ruslat);
        this.ruslat_state = false;

        this.sound = document.getElementById("sound");
        this.sound_enabled = false;

        this.ips = document.getElementById("ips");
        this.tps = document.getElementById("tps");

        this.meta_press_count = 0;

        this.configureEventListeners();

        setInterval(() => this.update_perf(), 2000);
    }

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

    configureEventListeners() {
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
            this.disassembler_visible = !this.disassembler_visible;
            this.disassembler_panel.style.display = this.disassembler_visible ? "block" : "none";
            this.disassembler_icon.src = "i/disassembler-" + (this.disassembler_visible ? "on" : "off") + ".svg";
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
                this.disassembler_panel.style.left = `${e.clientX - this.disassemblerOffsetX}px`;
                this.disassembler_panel.style.top = `${e.clientY - this.disassemblerOffsetY}px`;
            }
        });

        disassembler_panel.addEventListener("mouseup", () => {
            this.disassemberIsDragging = false;
        });

        document.onkeydown = (event) => {
            if (this.disassembler_visible) {
                const event = new KeyboardEvent("keydown", event);
                this.disassembler_panel.dispatchEvent(event);
            }
            if (this.meta_press_count > 0) {
                if (event.code === "KeyB") {
                    document.getElementById("sound").click();
                } else if (event.code === "KeyK") {
                    document.getElementById("file_selector").click();
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
            if (this.disassembler_visible) {
                const event = new KeyboardEvent("keyup", event);
                this.disassembler_panel.dispatchEvent(event);
            }
            if (event.key === "Meta") {
                if (this.meta_press_count > 0) this.meta_press_count -= 1;
                return;
            }
            if (this.meta_press_count > 0) return;

            this.machine.keyboard.onkeyup(event.code);
            return false;
        };
    }
}
