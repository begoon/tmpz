export class Tape {
    constructor(runner) {
        this.runner = runner;

        this.previous_bit_ticks = 0;
        this.bit_started = false;
        this.bit_count = 0;
        this.current_byte = 0;
        this.written_bytes = [];
        this.written_bytes_from_e6 = 0;
        this.output_block_count = 0;
        this.output_timer = null;
    }

    save(bytes) {
        const binary = new Uint8Array(bytes);
        const blob = new Blob([binary], { type: "image/gif" });
        const filename = `rk86-tape-${this.output_block_count}.bin`;
        Tape.saveAs(blob, filename);
        this.output_block_count += 1;
    }

    log(bytes) {
        for (let i = 0; i < bytes.length; i += 16) {
            const line = bytes.slice(i, i + 16);
            console.log(line.map((byte) => byte.toString(16).padStart(2, "0")).join(" "));
        }
    }

    write_ended() {
        this.bit_started = false;
        this.current_byte = 0;
        this.bit_count = 0;
        this.written_bytes = [];
        this.written_bytes_from_e6 = 0;
        this.update_activity_indicator(false);
        this.hightlight_written_bytes(false);
    }

    flush = () => {
        const sync_byte_index = this.written_bytes.findIndex((byte) => byte === 0xe6);
        if (sync_byte_index === -1) {
            console.error("sync byte E6 is not found");
            this.log(this.written_bytes);
        } else {
            console.log(`${sync_byte_index} bytes before sync byte`);
            const bytes = this.written_bytes.slice(sync_byte_index);
            this.log(bytes);
            this.save(bytes);
        }
        this.write_ended();
    };

    write_bit(bit) {
        const runner_ticks = this.runner.total_ticks;
        const time = runner_ticks - this.previous_bit_ticks;

        if (time > 10000) {
            // If there is no writes in ~5ms, reset the buffer, current
            // current_byte and bit counter.
            console.log("reset tape buffer due to timeout");
            this.write_ended();
        }

        if (!this.bit_started) {
            this.bit_started = true;
        } else {
            this.bit_started = false;
            this.current_byte |= (bit ? 0x80 : 0x00) >> this.bit_count;

            if (this.bit_count < 7) {
                this.bit_count += 1;
            } else {
                this.written_bytes.push(this.current_byte);

                if (this.current_byte === 0xe6 || this.written_bytes_from_e6 > 0) {
                    this.written_bytes_from_e6 += 1;
                }

                if (this.written_bytes.length === 1) this.update_activity_indicator(true);
                this.update_written_bytes(this.written_bytes_from_e6);

                if (this.output_timer) clearTimeout(this.output_timer);
                this.output_timer = setTimeout(this.flush, 1000);

                this.current_byte = 0;
                this.bit_count = 0;
            }
        }

        this.previous_bit_ticks = runner_ticks;
    }

    /**
     * @param {boolean} active - true if tape is active, false otherwise.
     */
    update_activity_indicator(active) {
        throw new Error("update_activity_indicator method must be set");
    }

    hightlight_written_bytes(state) {
        throw new Error("hightlight_written_bytes method must be set");
    }

    update_written_bytes(count) {
        throw new Error("update_written_bytes method must be set");
    }

    static saveAs(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.style.display = "none";
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    }
}
