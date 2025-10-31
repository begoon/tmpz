const std = @import("std");
const posix = std.posix;

const c = @cImport({
    @cInclude("termios.h");
    @cInclude("unistd.h");
});

// terminal raw/cooked helpers
fn set_raw(fd: posix.fd_t, orig: *c.termios) !void {
    if (c.tcgetattr(@as(i32, @intCast(fd)), orig) != 0) return error.TermiosGet;
    var raw = orig.*;
    c.cfmakeraw(&raw);
    // (optional) leave as full raw; Ctrl-C will appear as byte 0x03
    if (c.tcsetattr(@as(i32, @intCast(fd)), c.TCSANOW, &raw) != 0) return error.TermiosSet;
}

fn restore(fd: posix.fd_t, orig: *const c.termios) void {
    _ = c.tcsetattr(@as(i32, @intCast(fd)), c.TCSANOW, orig);
}

// minimal write/print helpers
fn write_all(fd: posix.fd_t, data: []const u8) !void {
    var off: usize = 0;
    while (off < data.len) {
        const n = try posix.write(fd, data[off..]);
        off += n;
    }
}

fn print_stderr(comptime fmt: []const u8, args: anytype) !void {
    var buf: [256]u8 = undefined;
    const str = try std.fmt.bufPrint(&buf, fmt, args);
    try write_all(posix.STDERR_FILENO, str);
}

// -- enable any-motion (1003) + SGR (1006)
fn enable_mouse() !void {
    try write_all(posix.STDOUT_FILENO, "\x1b[?1003h\x1b[?1006h");
}

// -- disable both 1003 and 1002 (be safe) + 1006
fn disable_mouse() void {
    _ = posix.write(posix.STDOUT_FILENO, "\x1b[?1003l\x1b[?1002l\x1b[?1006l") catch {};
}

// mouse event decoding
fn decode_button(btn: u32, endch: u8) struct {
    kind: []const u8,
    button: []const u8,
    shift: bool,
    meta: bool,
    ctrl: bool,
} {
    const is_move = (btn & 32) != 0;
    const is_wheel = (btn & 64) != 0;
    const shift = (btn & 4) != 0;
    const meta = (btn & 8) != 0;
    const ctrl = (btn & 16) != 0;
    const base = btn & 3;

    var kind: []const u8 = "press";
    if (endch == 'm') kind = "release";
    if (is_move) kind = "move";

    var button: []const u8 = switch (base) {
        0 => "left",
        1 => "middle",
        2 => "right",
        else => "unknown",
    };

    if (is_wheel) {
        button = if (base == 0) "wheel_up" else "wheel_down";
        kind = "scroll";
    }

    return .{ .kind = kind, .button = button, .shift = shift, .meta = meta, .ctrl = ctrl };
}

// Parse ESC [ < b ; x ; y (M|m); print; return bytes consumed.
fn parse_and_print(buf: []const u8) !usize {
    var i: usize = 0;
    var consumed: usize = 0;

    while (i + 6 <= buf.len) {
        if (!(buf[i] == 0x1b and i + 2 < buf.len and buf[i + 1] == '[' and buf[i + 2] == '<')) {
            i += 1;
            continue;
        }
        var j = i + 3;

        var b: u32 = 0;
        var found = false;
        while (j < buf.len and buf[j] >= '0' and buf[j] <= '9') : (j += 1) {
            found = true;
            b = b * 10 + (buf[j] - '0');
        }
        if (!found or j >= buf.len or buf[j] != ';') break;
        j += 1;

        var x: u32 = 0;
        found = false;
        while (j < buf.len and buf[j] >= '0' and buf[j] <= '9') : (j += 1) {
            found = true;
            x = x * 10 + (buf[j] - '0');
        }
        if (!found or j >= buf.len or buf[j] != ';') break;
        j += 1;

        var y: u32 = 0;
        found = false;
        while (j < buf.len and buf[j] >= '0' and buf[j] <= '9') : (j += 1) {
            found = true;
            y = y * 10 + (buf[j] - '0');
        }
        if (!found or j >= buf.len) break;

        const endch = buf[j];
        if (endch != 'M' and endch != 'm') break;
        j += 1;

        const info = decode_button(b, endch);
        try print_stderr(
            "event={s} button={s} x={} y={} modifiers=[{s}{s}{s}]\n\r",
            .{
                info.kind,
                info.button,
                x,
                y,
                if (info.shift) "shift" else "",
                if (info.meta) (if (info.shift) ", meta" else "meta") else "",
                if (info.ctrl) (if (info.shift or info.meta) ", ctrl" else "ctrl") else "",
            },
        );

        consumed = j;
        i = j;
    }

    return consumed;
}

pub fn main() !void {
    const fd_in: posix.fd_t = posix.STDIN_FILENO;

    var orig: c.termios = undefined;
    try set_raw(fd_in, &orig);
    defer restore(fd_in, &orig);

    try enable_mouse();
    defer disable_mouse();

    try print_stderr("mouse tracking enabled (?1003 + ?1006). Press Ctrl-C to quit.\n\r", .{});

    var carry: [4096]u8 = undefined; // rolling buffer for partial sequences
    var carry_len: usize = 0;

    var buf: [512]u8 = undefined;

    while (true) {
        const n = try posix.read(fd_in, buf[0..]);
        if (n == 0) break;

        // --- handle Ctrl-C (0x03) in raw mode ---
        if (std.mem.indexOfScalar(u8, buf[0..n], 3) != null) {
            try print_stderr("\n\r^C detected, exiting...\n\r", .{});
            break;
        }

        // append to carry (truncate if overflow)
        const to_copy = n;
        if (carry_len + to_copy > carry.len) {
            const excess = carry_len + to_copy - carry.len;
            if (excess < carry_len) {
                std.mem.copyForwards(u8, carry[0 .. carry_len - excess], carry[excess..carry_len]);
                carry_len -= excess;
            } else {
                carry_len = 0;
            }
        }
        std.mem.copyForwards(u8, carry[carry_len .. carry_len + to_copy], buf[0..to_copy]);
        carry_len += to_copy;

        // parse as much as possible
        const consumed = try parse_and_print(carry[0..carry_len]);
        if (consumed > 0) {
            const rem = carry_len - consumed;
            std.mem.copyForwards(u8, carry[0..rem], carry[consumed..carry_len]);
            carry_len = rem;
        }
    }
}
