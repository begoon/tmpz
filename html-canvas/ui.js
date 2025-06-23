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
        this.machine.keyboard.reset();
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
        this.ruslat.textContent = value ? "РУС" : "ЛАТ";
    };

    document.getElementById("ruslat-toggle").addEventListener("click", () => {
        // Конкретный адрес флага раскладки оригинального монитора 32КБ.
        const ruslat_flag = 0x7606;
        const state = this.machine.memory.read(ruslat_flag) ? 0x00 : 0xff;
        this.machine.memory.write(ruslat_flag, state);
        this.update_ruslat(state);
    });

    this.sound = document.getElementById("sound");
    this.sound_enabled = false;

    this.sound.addEventListener("click", () => {
        this.sound_enabled = !this.sound_enabled;
        this.machine.runner.init_sound(this.sound_enabled);
        console.log("sound " + (this.sound_enabled ? "enabled" : "disabled"));

        const icon_toggle = document.getElementById("sound-icon-toggle");
        icon_toggle.src = this.sound_enabled ? icon_toggle.dataset.on : icon_toggle.dataset.muted;

        const icon = document.getElementById("sound-icon");
        icon.textContent = icon.dataset[this.sound_enabled ? "on" : "off"];
        icon.classList.add("visible");
        setTimeout(() => icon.classList.remove("visible"), 2000);
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

    this.update_video_memory_base = (base) => {
        document.getElementById("video-base").textContent = base.toString(16).toUpperCase();
    };

    this.update_screen_geometry = (width, height) => {
        document.getElementById("video-width").textContent = width.toString();
        document.getElementById("video-height").textContent = height.toString();
    };

    this.meta_press_count = 0;
    document.onkeydown = (event) => {
        console.log("onkeydown", this.meta_press_count, "code", event.code, "key", event.key);
        if (this.meta_press_count > 0) {
            if (event.code === "KeyB") {
                document.getElementById("sound").click();
                console.log("Sound toggle");
            } else if (event.code === "KeyK") {
                document.getElementById("file_selector").click();
            }
            return;
        }

        if (event.key === "Meta") {
            this.meta_press_count += 1;
            return;
        }

        machine.keyboard.onkeydown(event.code);
        return false;
    };

    document.onkeyup = (event) => {
        console.log("onkeyup", this.meta_press_count, "code", event.code, "key", event.key);

        if (event.key === "Meta") {
            if (this.meta_press_count > 0) this.meta_press_count -= 1;
            return;
        }
        if (this.meta_press_count > 0) return;

        machine.keyboard.onkeyup(event.code);
        return false;
    };
}
