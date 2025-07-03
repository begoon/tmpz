// import Terminal from "./termlib/termlib.js";
// import Parser from "./termlib/termlib_parser.js";
import "./format.js";
import { Terminal } from "./xterm.mjs";
// import "https://esm.sh/xterm@5.3.0/css/xterm.css";
import { hex16 } from "./hex.js";
import { i8080_opcode } from "./i8080_disasm.js";
import { saveAs } from "./saver.js";

export function parseNumber(str) {
    if (typeof str !== "string" || str.length === 0) return NaN;
    str = str.trim();
    if (str.startsWith("$")) str = "0x" + str.slice(1);
    else if (str.endsWith("h")) str = "0x" + str.slice(0, -1);
    else if (str.match(/^[a-f]/i)) str = "0x" + str;
    console.log(`parseNumber: str = [${str}]`);
    return parseInt(str);
}

export function Console(machine) {
    const from_rk86_table = [
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [" ", "!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/"],
        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?"],
        ["@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"],
        ["P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\", "]", "^", "_"],
        ["Ю", "А", "Б", "Ц", "Д", "Е", "Ф", "Г", "Х", "И", "Й", "К", "Л", "М", "Н", "О"],
        ["П", "Я", "Р", "С", "Т", "У", "Ж", "В", "Ь", "Ы", "З", "Ш", "Э", "Щ", "Ч", "~"],
    ].flat();

    // this.dump_cmd_last_address = 0;
    // this.dump_cmd_last_length = 128;

    this.dump_cmd = (args) => {
        let from = parseNumber(args[0]);
        if (isNaN(from)) from = this.dump_cmd.last_address || 0;

        let sz = parseNumber(args[1]);
        if (isNaN(sz)) sz = this.dump_cmd.last_length || 128;
        this.dump_cmd.last_length = sz;

        const { memory } = machine;

        const WIDTH = 16;
        while (sz > 0) {
            let bytes = "";
            let chars = "";
            const chunk_sz = Math.min(WIDTH, sz);
            for (let i = 0; i < chunk_sz; ++i) {
                const byte = memory.read_raw(from + i);
                bytes += "%02X ".format(byte);
                chars += byte >= 32 && byte < 127 ? from_rk86_table[byte] : ".";
            }
            if (sz < WIDTH) {
                bytes += " ".repeat((WIDTH - sz) * 3);
                chars += " ".repeat(WIDTH - sz);
            }
            this.term.writeln("%04X: %s | %s".format(from, bytes, chars));
            sz -= chunk_sz;
            from = (from + chunk_sz) & 0xffff;
        }
        this.dump_cmd.last_address = from;
    };

    this.download_cmd = (args) => {
        let from = parseNumber(args[0]);
        if (isNaN(from)) from = this.download_cmd.snapshot_address || 0;
        this.download_cmd.snapshot_address = from;

        let sz = parseNumber(args[1]);
        if (isNaN(sz)) sz = this.download_cmd.snapshot_length || 0x8000;
        this.download_cmd.snapshot_length = sz;

        this.download_cmd.filename_count = this.download_cmd.filename_count || 1;
        const filename = "rk86-memory-%04X-%04X-%d.bin".format(from, sz, this.download_cmd.filename_count);

        console.log(`download ${hex16(from)}:${hex16(sz)} -> ${filename}`);

        const { memory } = machine;
        const content = memory.snapshot(from, sz);
        const blob = new Blob([new Uint8Array(content)], { type: "application/octet-stream" });

        saveAs(blob, filename);

        this.download_cmd.filename_count += 1;
    };

    this.disasm_print = (addr, nb_instr, current_addr) => {
        const { memory } = machine;
        while (nb_instr-- > 0) {
            let binary = [];
            for (let i = 0; i < 3; ++i) binary[binary.length] = memory.read_raw(addr + i);
            const instr = i8080_opcode(...binary);

            let bytes = "";
            let chars = "";
            for (let i = 0; i < instr.length; ++i) {
                const byte = binary[i];
                bytes += "%02X".format(byte);
                chars += byte >= 32 && byte < 127 ? from_rk86_table[byte] : ".";
            }
            bytes += " ".repeat((binary.length - instr.length) * 2);
            chars += " ".repeat(binary.length - instr.length);

            const current = current_addr && addr == current_addr ? ">" : " ";
            this.term.writeln("%04X: %s%s %s %s".format(addr, current, bytes, chars, instr.cmd));
            addr += instr.length;
        }
        return addr;
    };

    this.cpu_cmd = (args) => {
        const { cpu, runner, memory } = machine;
        this.term.write(
            "PC=%04X A=%02X F=%s%s%s%s%s HL=%04X DE=%04X BC=%04X SP=%04X".format(
                cpu.pc,
                cpu.a(),
                cpu.cf ? "C" : "-",
                cpu.pf ? "P" : "-",
                cpu.hf ? "H" : "-",
                cpu.zf ? "Z" : "-",
                cpu.sf ? "S" : "-",
                cpu.hl(),
                cpu.de(),
                cpu.bc(),
                cpu.sp
            )
        );
        this.term.writeln("");

        const { last_instructions } = runner;
        for (let i = 0; i < last_instructions.length; ++i) {
            const addr = last_instructions[i];
            this.disasm_print(addr, 1, cpu.pc);
        }
        this.disasm_print(cpu.pc, 5, cpu.pc);

        const hex = (addr, title) => {
            let bytes = "";
            let chars = "";
            for (let i = 0; i < 16; ++i) {
                const byte = memory.read_raw(addr + i);
                bytes += "%02X ".format(byte);
                chars += byte >= 32 && byte < 127 ? from_rk86_table[byte] : ".";
            }
            this.term.writeln("%s=%04X: %s | %s".format(title, addr, bytes, chars));
        };

        hex(cpu.pc, "PC");
        hex(cpu.sp, "SP");
        hex(cpu.hl(), "HL");
        hex(cpu.de(), "DE");
        hex(cpu.bc(), "BC");
    };

    this.disasm_cmd = (args) => {
        const { cpu } = machine;

        let from = parseNumber(args[0]);
        if (isNaN(from)) from = this.disasm_cmd.last_address || cpu.pc;

        let sz = parseNumber(args[1]);
        if (isNaN(sz)) sz = this.disasm_cmd.last_length || 16;
        this.disasm_cmd.last_length = sz;

        this.disasm_cmd.last_address = this.disasm_print(from, sz);
    };

    this.write_byte_cmd = (args) => {
        const { memory } = machine;

        if (args.length < 2) {
            this.term.write("?");
            return;
        }

        let addr = parseNumber(args.shift());
        if (isNaN(addr)) addr = 0;

        for (let i = 0; i < args.length; ++i) {
            const byte = parseNumber(args[i]);
            if (isNaN(byte)) break;
            this.term.writeln("%04X: %02X -> %02X".format(addr, memory.read_raw(addr), byte));
            memory.write_raw(addr, byte);
            addr = (addr + 1) & 0xffff;
        }
    };

    this.write_word_cmd = (args) => {
        const { memory } = machine;

        if (args.length < 2) {
            this.term.write("?");
            return;
        }

        let addr = parseNumber(args.shift());
        if (isNaN(addr)) addr = 0;

        for (let i = 0; i < args.length; ++i) {
            const w16 = parseNumber(args[i]);
            if (isNaN(w16)) break;
            const l = w16 & 0xff;
            const h = w16 >> 8;

            this.term.writeln("%04X: %02X -> %02X".format(addr, memory.read_raw(addr), l));
            memory.write_raw(addr, l);
            addr = (addr + 1) & 0xffff;

            this.term.writeln("%04X: %02X -> %02X".format(addr, memory.read_raw(addr), h));
            memory.write_raw(addr, h);
            addr = (addr + 1) & 0xffff;
        }
    };

    this.write_char_cmd = (args) => {
        const { memory } = machine;

        if (args.length < 2) {
            this.term.write("?");
            return;
        }
        let addr = parseNumber(args.shift());
        if (isNaN(addr)) addr = 0;

        let s = args[0];
        if (!s || s.length == 0) return;

        for (let i = 0; i < s.length; ++i) {
            const ch = s.charCodeAt(i) & 0xff;

            this.term.writeln("%04X: %02X -> %02X".format(addr, memory.read_raw(addr), ch));
            memory.write_raw(addr, ch);
            addr = (addr + 1) & 0xffff;
        }
    };

    this.print_breakpoint = function (self, n, b) {
        this.term.write(
            "Breakpoint #%s %s %s %04X".format(n, b.type, b.active == "yes" ? "active" : "disabled", b.address)
        );
        if (b.count) this.term.write(" count:%d/%d".format(b.count, b.hits));
        this.term.writeln("");
    };

    this.execute_after_breakpoint = false;

    this.process_breakpoint = function (self, i, b) {
        this.print_breakpoint(self, i, b);
        this.pause_cmd(this);
        this.term.prompt();
        window.focus();
        this.execute_after_breakpoint = true;
    };

    this.stop_after_next_instruction = -1;
    this.step_over_address = -1;

    this.tracer_callback = function (self, cpu, when) {
        // After entering into the single step mode ('s' command) we have to
        // execute one instruction (because CPU commands are executed AFTER
        // processing console commands) and then stop before the next one.
        // So the 's' command sets "stop_after_next_instruction" to 0, we
        // catch that in this callback, execute and current command, then set
        // "stop_after_next_instruction" to 1 and then use this as the
        // condition to stop before the next instruction.
        if (this.stop_after_next_instruction == 1) {
            this.pause_cmd(this);
            this.term.prompt();
            this.stop_after_next_instruction = -1;
            return;
        }

        if (this.stop_after_next_instruction == 0) this.stop_after_next_instruction = 1;

        // After hitting a breakpoint, we have to forcibly execute the current
        // instruction. Otherwise it will hit the same breakpoint immediatelly
        // and execution will be stuck.
        if (this.execute_after_breakpoint) {
            this.execute_after_breakpoint = false;
            return false;
        }

        function breakpoint_hit(breakpoint, breakpoint_index) {
            if (!b.count) {
                this.process_breakpoint(self, breakpoint_index, breakpoint);
            } else {
                ++b.hits;
                if (b.hits == b.count) {
                    this.process_breakpoint(self, breakpoint_index, breakpoint);
                    b.hits = 0;
                }
            }
            if (b.temporary == "yes") this.breaks[i] = null;
        }

        for (var i in this.breaks) {
            var b = this.breaks[i];
            if (b == null || b.active != "yes") continue;
            // Process "exec" breakpoints only before the current instruction.
            if (when == "before" && b.address == cpu.pc && b.type == "exec") {
                breakpoint_hit(b, i);
            }
            // Process "read/write" breakpoints only after the current instruction.
            if (when == "after") {
                var address = cpu.memory.last_access_address;
                var operation = cpu.memory.last_access_operation;
                if (b.address == address && b.type == operation) {
                    breakpoint_hit(b, i);
                }
            }
        }
    };

    this.debug_cmd = (args) => {
        var state = this.term.argv[1];
        var tracer = this.runner.tracer;

        if (state == "on" || state == "off") {
            if (state == "on") {
                this.term.writeln("Tracing is on");
                this.runner.tracer = function (when) {
                    var cpu = this.runner.cpu;
                    return this.tracer_callback(self, cpu, when);
                };
            } else {
                this.runner.tracer = null;
                this.term.write("Tracing is off");
            }
        } else {
            this.term.write("Trace is %s".format(tracer ? "on" : "off"));
        }
    };

    this.check_tracer_active = (args) => {
        if (this.runner.tracer == null) {
            this.term.writeln("Tracing is not active. Use 't' command to activate.");
            return false;
        }
        return true;
    };

    this.list_breakpoints_cmd = (args) => {
        for (var i in this.breaks) {
            var b = this.breaks[i];
            if (b == null) continue;
            this.print_breakpoint(self, i, b);
        }
    };

    this.edit_breakpoints_cmd = (args) => {
        var term = this.term;

        if (this.term.argc < 3) {
            term.write("?");
            return;
        }
        var n = parseInt(term.argv[1]);
        if (isNaN(n)) {
            term.write("?");
            return;
        }
        if (this.breaks[n] == null) this.breaks[n] = { type: "?", active: "no", address: 0 };
        var b = this.breaks[n];

        for (var i = 2; i < this.term.argc; ++i) {
            var args = term.argv[i].split(/[:=]/);
            var arg = args.shift();
            var value = args.shift();
            if (["count", "address", "hits"].indexOf(arg) != -1) {
                var num = parseInt(value);
                if (isNaN(num)) {
                    term.write("?");
                    return;
                }
                b[arg] = num;
                if (arg == "count") b.hits = 0;
            } else b[arg] = value;
        }
    };

    this.delete_breakpoints_cmd = (args) => {
        var term = this.term;

        if (this.term.argc < 2) {
            term.write("?");
            return;
        }
        var n = parseInt(term.argv[1]);
        if (isNaN(n)) {
            term.write("?");
            return;
        }

        this.breaks[n] = null;
    };

    this.pause_cmd = (args) => {
        this.runner.pause();
        this.pause();
        this.ui.update_pause_button(this.runner.paused);
    };

    this.resume_cmd = (args) => {
        this.runner.resume();
        this.resume();
        this.ui.update_pause_button(this.runner.paused);
        window.opener.focus();
    };

    this.reset_cmd = (args) => {
        this.ui.reset();
        window.opener.focus();
    };

    this.restart_cmd = (args) => {
        this.ui.restart();
        window.opener.focus();
    };

    this.go_cmd = (args) => {
        if (this.term.argc < 2) {
            this.term.write("?");
            return;
        }
        var addr = parseInt(this.term.argv[1]);
        if (isNaN(addr)) {
            this.term.write("?");
            return;
        }
        this.runner.cpu.jump(addr);
    };

    this.single_step_cmd = (args) => {
        if (!this.check_tracer_active(self)) return;
        this.stop_after_next_instruction = 0;
        this.resume_cmd(self);
    };

    this.step_over_cmd = (args) => {
        var cpu = this.runner.cpu;
        var mem = cpu.memory;
        var binary = [];
        for (var i = 0; i < 3; ++i) binary[binary.length] = mem.read_raw(cpu.pc + i);
        var instr = i8080_disasm(binary);
        var b = {
            type: "exec",
            address: (cpu.pc + instr.length) & 0xffff,
            active: "yes",
            temporary: "yes",
        };
        this.breaks[1000] = b;
        this.resume_cmd(self);
    };

    this.check_sum_cmd = (args) => {
        if (this.term.argc < 3) {
            this.term.write("?");
            return;
        }
        var from = parseInt(this.term.argv[1]);
        if (isNaN(from)) {
            this.term.write("?");
            return;
        }
        var to = parseInt(this.term.argv[2]);
        if (isNaN(to)) {
            this.term.write("?");
            return;
        }
        const image = this.runner.cpu.memory.snapshot(from, to + 1 - from);
        const checksum = rk86_check_sum(image);
        this.term.writeln("%04X-%04X: %04X".format(from, to, checksum));
    };

    this.help_cmd = (args) => {
        for (var cmd in this.commands) {
            this.term.writeln("%s - %s".format(cmd, this.commands[cmd][1]));
        }
    };

    this.commands = {
        d: [this.dump_cmd, "dump memory / d [start_address[, number_of_bytes]]"],
        dd: [this.download_cmd, "download memory / dd [start_address=0 [, number_of_bytes=0x8000]]"],
        i: [this.cpu_cmd, "CPU iformation / i"],
        z: [this.disasm_cmd, "disassemble / z [start_address [, number_of_instructions]]"],
        w: [this.write_byte_cmd, "write bytes / w start_address byte1, [byte2, [byte3]...]"],
        ww: [this.write_word_cmd, "write words / ww start_address word1, [word2, [word3]...]"],
        wc: [this.write_char_cmd, "write characters / ww start_address string"],
        t: [this.debug_cmd, "debug control / t [on|off]"],
        p: [this.pause_cmd, "pause CPU / p"],
        r: [this.resume_cmd, "resume CPU / r"],
        g: [this.go_cmd, "go to an address / g 0xf86c"],
        gr: [this.reset_cmd, "reset / gr"],
        gs: [this.restart_cmd, "restart / gs"],
        s: [this.single_step_cmd, "single step"],
        so: [this.step_over_cmd, "step over"],
        bl: [this.list_breakpoints_cmd, "list breakpoints / bl"],
        be: [this.edit_breakpoints_cmd, "create/edit breakpoints / be 1 type:exec address:0xf86c count:3"],
        bd: [this.delete_breakpoints_cmd, "delete breakpoints / bd 1"],
        cs: [this.check_sum_cmd, "calculate checksum / cs start_address, end_address"],
        "?": [this.help_cmd, "this help / ?"],
    };

    this.breaks = {
        1: { type: "exec", address: 0xf86c, active: "no", count: 0, hits: 0 },
        2: { type: "read", address: 0x0100, active: "no", count: 0, hits: 0 },
        3: { type: "write", address: 0x0200, active: "no", count: 0, hits: 0 },
        4: { type: "exec", address: 0xfca5, active: "no", count: 7, hits: 0 },
    };

    this.argc = 0;
    this.argv = [];

    this.command = function (line) {
        line = line.trim();
        if (line.length == 0) return;
        // console.log(`command [${line}]`);
        this.argv = line.split(/\s+/);
        this.argc = this.argv.length;
        // console.log("argc", this.argc, "argv", this.argv);

        this.term.writeln("");

        if (this.argv.length > 0) {
            const cmd = this.argv[0];
            // cmd = cmd.toLowerCase();
            const args = this.argv.slice(1);
            const handler = this.commands[cmd.toLowerCase()];
            if (handler) handler[0](args);
            else this.term.write("?");
        }
        this.term.prompt();
    };

    let line_buffer = "";

    let history = [];
    let history_index = -1;

    this.press = (data) => {
        console.log("press", `${data.length}: [${data}] [${line_buffer}]`);
        const strokes = [
            [
                "\r",
                () => {
                    let cleared = line_buffer.trim();
                    line_buffer = "";
                    if (cleared.length === 0) {
                        if (history.length === 0) return;
                        cleared = history.at(-1);
                    }
                    if (history.at(-1) !== cleared) {
                        history.push(cleared);
                        history_index = history.length - 1;
                    }
                    this.term.writeln("");
                    this.command(cleared);
                },
            ],
            [
                ["\x7f", "\x1b[D"],
                () => {
                    if (line_buffer.length > 0) {
                        this.term.write("\b \b");
                        line_buffer = line_buffer.slice(0, -1);
                    }
                },
            ],
            [
                "\x1b[A",
                () => {
                    if (history_index === -1) return;
                    const cmd = history[history_index];
                    if (history_index > 0) history_index -= 1;
                    this.term.write("\r\x1b[0K> " + cmd);
                    line_buffer = cmd;
                },
            ],
            [
                "\x1b[B",
                () => {
                    if (history_index === -1) return;
                    if (history_index < history.length - 1) history_index += 1;
                    const cmd = history[history_index];
                    this.term.write("\r\x1b[0K> " + cmd);
                    line_buffer = cmd;
                },
            ],
            [
                ["\x1b", "\x03"],
                () => {
                    this.term.write("\r\x1b[0K> ");
                    line_buffer = "";
                },
            ],
        ];
        const stroke = strokes.find(([prefix, _]) => [prefix].flat().some((v) => data.startsWith(v)));
        if (stroke) {
            const [prefix, action] = stroke;
            action();
            data = data.slice(prefix.length);
        } else {
            const first = data.at(0);
            line_buffer += first;
            this.term.write(first);
            data = data.slice(1);
        }
    };

    this.init = (machine) => {
        this.ui = machine.ui;
        this.runner = machine.runner;

        this.term = new Terminal({ cols: 80, rows: 24, theme: { foreground: "#00ff00" } });
        this.term.prompt = () => this.term.write("\r\n> ");

        this.term.open(document.getElementById("console"));

        this.term.textarea.addEventListener("keydown", (e) => e.stopPropagation());

        this.term.attachCustomKeyEventHandler((ev) => {
            if (ev.key === " ") {
                ev.preventDefault();
                if (ev.type === "keydown") this.term.input(ev.key);
            }
            return true;
        });

        this.term.onData((data) => {
            console.log(
                "onData",
                data.length,
                data.split("").map((c) => c.charCodeAt(0))
            );
            this.press(data);
        });

        this.term.writeln("Консоль Радио-86РК / ? - команды");
        this.term.focus();
        this.term.prompt();
    };

    this.pause = function () {
        this.term.writeln("Paused at %04X".format(this.runner.cpu.pc));
        this.cpu_cmd(this);
    };

    this.pause_ui_callback = function () {
        this.pause();
        this.term.prompt();
    };

    this.resume = function () {
        this.term.write("Resumed");
    };

    this.resume_ui_callback = function () {
        this.resume();
        this.term.prompt();
    };

    this.init(machine);
}
