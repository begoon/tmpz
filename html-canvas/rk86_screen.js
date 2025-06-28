export class Screen {
    static #update_rate = 25;

    constructor(machine) {
        this.machine = machine;

        this.cursor_rate = 500;

        this.char_width = 6;
        this.char_height = 8;
        this.char_height_gap = 2;

        this.cursor_width = this.char_width;
        this.cursor_height = 1;
        this.cursor_offset_white = 27;

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
        this.font.src = this.machine.font;

        this.light_pen_x = 0;
        this.light_pen_y = 0;
        this.light_pen_active = 0;

        this.last_video_memory_base = -1;
        this.last_video_memory_size = -1;

        this.init();
        this.flip_cursor();
        this.draw_screen();

        this.machine.ui.canvas.onmousemove = this.handle_mousemove.bind(this);
        this.machine.ui.canvas.onmouseup = () => {
            this.light_pen_active = 0;
        };
        this.machine.ui.canvas.onmousedown = () => {
            this.light_pen_active = 1;
        };
    }

    init_cache(sz) {
        for (let i = 0; i < sz; ++i) {
            this.cache[i] = true;
        }
    }

    draw_char(x, y, ch) {
        this.ctx.drawImage(
            this.font,
            2,
            this.char_height * ch,
            this.char_width,
            this.char_height,
            x * this.char_width * this.scale_x,
            y * (this.char_height + this.char_height_gap) * this.scale_y,
            this.char_width * this.scale_x,
            this.char_height * this.scale_y
        );
    }

    draw_cursor(x, y, visible) {
        this.ctx.drawImage(
            this.font,
            2,
            this.cursor_offset_white + (visible ? 0 : 1),
            this.char_width,
            1,
            x * this.char_width * this.scale_x,
            (y * (this.char_height + this.char_height_gap) + this.char_height) * this.scale_y,
            this.char_width * this.scale_x,
            1 * this.scale_y
        );
    }

    flip_cursor() {
        this.draw_cursor(this.cursor_x, this.cursor_y, this.cursor_state);
        this.cursor_state = !this.cursor_state;
        setTimeout(() => this.flip_cursor(), this.cursor_rate);
    }

    init() {
        this.ctx = this.machine.ui.canvas.getContext("2d");
    }

    disable_smoothing() {
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.imageSmoothingEnabled = false;
    }

    set_geometry(width, height) {
        this.width = width;
        this.height = height;
        this.video_memory_size = width * height;

        this.machine.ui.update_screen_geometry(this.width, this.height);
        console.log(`screen geometry: ${width} x ${height}`);

        const canvas_width = this.width * this.char_width * this.scale_x;
        const canvas_height = this.height * (this.char_height + this.char_height_gap) * this.scale_y;
        this.machine.ui.resize_canvas(canvas_width, canvas_height);

        this.disable_smoothing();
        this.ctx.fillRect(0, 0, canvas_width, canvas_height);
    }

    set_video_memory(base) {
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
    }

    set_cursor(x, y) {
        this.draw_cursor(this.cursor_x, this.cursor_y, false);
        this.cursor_x = x;
        this.cursor_y = y;
    }

    draw_screen() {
        const memory = this.machine.memory;
        let i = this.video_memory_base;
        for (let y = 0; y < this.height; ++y) {
            for (let x = 0; x < this.width; ++x) {
                const cache_i = i - this.video_memory_base;
                const ch = memory.read(i);
                if (this.cache[cache_i] !== ch) {
                    this.draw_char(x, y, ch);
                    this.cache[cache_i] = ch;
                }
                i += 1;
            }
        }
        setTimeout(() => this.draw_screen(), Screen.update_rate);
    }

    handle_mousemove(event) {
        const canvas = this.machine.ui.canvas;
        const x = Math.floor((event.x + 1 - canvas.offsetLeft) / (this.char_width * this.scale_x));
        const y = Math.floor(
            (event.y + 1 - canvas.offsetTop) / ((this.char_height + this.char_height_gap) * this.scale_y)
        );
        this.light_pen_x = x;
        this.light_pen_y = y;
    }
}
