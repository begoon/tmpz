const std = @import("std");
const Io = std.Io;
const posix = std.posix;

const special_prefixes = [_][]const u8{
    "/opt/homebrew",
    "/opt/workbrew",
    "/opt/zerobrew",
};

// ANSI escape codes
const RESET = "\x1b[0m";
const BLUE = "\x1b[34m";
const YELLOW = "\x1b[33m";
const WHITE = "\x1b[97m";
const DIM = "\x1b[2m";
const STRIKE = "\x1b[9m";
const REVERSE = "\x1b[7m";
const BOLD = "\x1b[1m";
const HIDE_CURSOR = "\x1b[?25l";
const SHOW_CURSOR = "\x1b[?25h";
const CLEAR_LINE = "\x1b[2K";
const CLEAR_SCREEN = "\x1b[2J";
const CURSOR_HOME = "\x1b[H";

/// Returns the length of a matching special prefix, or null if none match.
/// Only matches at path boundaries (exact match or followed by '/').
pub fn findSpecialPrefix(path: []const u8) ?usize {
    for (special_prefixes) |prefix| {
        if (path.len >= prefix.len and
            std.mem.eql(u8, path[0..prefix.len], prefix) and
            (path.len == prefix.len or path[prefix.len] == '/'))
        {
            return prefix.len;
        }
    }
    return null;
}

/// If path starts with home dir, returns the suffix after home and is_home=true.
/// Ensures match is at a path boundary.
pub fn shortenHome(path: []const u8, home: []const u8) struct { suffix: []const u8, is_home: bool } {
    if (home.len > 0 and path.len >= home.len and
        std.mem.eql(u8, path[0..home.len], home) and
        (path.len == home.len or path[home.len] == '/'))
    {
        return .{ .suffix = path[home.len..], .is_home = true };
    }
    return .{ .suffix = path, .is_home = false };
}

fn countEntries(io: Io, path: []const u8) struct { count: usize, exists: bool } {
    const dir = (if (std.fs.path.isAbsolute(path))
        Io.Dir.openDirAbsolute(io, path, .{ .iterate = true })
    else
        Io.Dir.cwd().openDir(io, path, .{ .iterate = true })) catch
        return .{ .count = 0, .exists = false };
    var d = dir;
    defer d.close(io);

    var count: usize = 0;
    var iter = d.iterate();
    while (iter.next(io) catch null) |entry| {
        if (entry.kind != .directory) {
            count += 1;
        }
    }
    return .{ .count = count, .exists = true };
}

fn printEntry(writer: anytype, io: Io, path: []const u8, home: []const u8) !void {
    const info = countEntries(io, path);
    const shortened = shortenHome(path, home);

    if (!info.exists) {
        try writer.writeAll(STRIKE);
        if (shortened.is_home) {
            try writer.writeAll(WHITE ++ "~");
            try writer.writeAll(shortened.suffix);
            try writer.writeAll(RESET);
        } else {
            try writer.writeAll(path);
            try writer.writeAll(RESET);
        }
        try writer.writeAll(" \xe2\x9d\x8c");
    } else if (shortened.is_home) {
        try writer.writeAll(YELLOW ++ "~");
        try writer.writeAll(shortened.suffix);
        try writer.writeAll(RESET);
    } else if (findSpecialPrefix(path)) |prefix_len| {
        try writer.writeAll(BLUE);
        try writer.writeAll(path[0..prefix_len]);
        try writer.writeAll(RESET);
        try writer.writeAll(path[prefix_len..]);
    } else {
        try writer.writeAll(path);
    }

    try writer.print(DIM ++ " ({d})" ++ RESET ++ "\n", .{info.count});
}

fn detectTerminalHeight() u16 {
    var wsz: posix.winsize = .{ .row = 24, .col = 80, .xpixel = 0, .ypixel = 0 };
    const r = std.c.ioctl(std.posix.STDOUT_FILENO, std.posix.T.IOCGWINSZ, @intFromPtr(&wsz));
    if (r == 0) return wsz.row;
    return 24;
}

fn enableRawMode() std.posix.termios {
    const orig = std.posix.tcgetattr(std.posix.STDIN_FILENO) catch unreachable;
    var raw = orig;
    raw.lflag.ECHO = false;
    raw.lflag.ICANON = false;
    raw.lflag.ISIG = false;
    raw.cc[@intFromEnum(std.posix.V.MIN)] = 1;
    raw.cc[@intFromEnum(std.posix.V.TIME)] = 0;
    std.posix.tcsetattr(std.posix.STDIN_FILENO, .FLUSH, raw) catch unreachable;
    return orig;
}

fn disableRawMode(orig: std.posix.termios) void {
    std.posix.tcsetattr(std.posix.STDIN_FILENO, .FLUSH, orig) catch {};
}

fn writeAll(buf: []const u8) void {
    var offset: usize = 0;
    while (offset < buf.len) {
        const n = std.c.write(std.posix.STDOUT_FILENO, buf[offset..].ptr, buf.len - offset);
        if (n < 0) return;
        offset += @intCast(n);
    }
}

fn writeFmt(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, fmt, args) catch return;
    writeAll(s);
}

fn readKey() enum { up, down, enter, quit, other } {
    var buf: [8]u8 = undefined;
    const rc = std.c.read(std.posix.STDIN_FILENO, &buf, buf.len);
    if (rc <= 0) return .quit;
    const n: usize = @intCast(rc);

    if (buf[0] == 'q' or buf[0] == 'Q') return .quit;
    if (buf[0] == 27) { // ESC
        if (n == 1) return .quit;
        if (n >= 3 and buf[1] == '[') {
            if (buf[2] == 'A') return .up;
            if (buf[2] == 'B') return .down;
        }
        return .other;
    }
    if (buf[0] == '\r' or buf[0] == '\n') return .enter;
    if (buf[0] == 'k' or buf[0] == 'K') return .up;
    if (buf[0] == 'j' or buf[0] == 'J') return .down;
    return .other;
}

fn renderList(
    paths: []const []const u8,
    home: []const u8,
    selected: usize,
    scroll_offset: usize,
    visible_count: usize,
    io: Io,
) void {
    writeAll(CURSOR_HOME);

    for (0..visible_count) |i| {
        const idx = scroll_offset + i;
        writeAll(CLEAR_LINE);
        if (idx < paths.len) {
            const path = paths[idx];
            const info = countEntries(io, path);
            const shortened = shortenHome(path, home);

            if (idx == selected) {
                writeAll(REVERSE ++ BOLD);
            }

            if (!info.exists) {
                writeAll(STRIKE);
                if (shortened.is_home) {
                    writeAll("~");
                    writeAll(shortened.suffix);
                } else {
                    writeAll(path);
                }
                writeAll(" \xe2\x9d\x8c");
            } else if (shortened.is_home) {
                if (idx != selected) writeAll(YELLOW);
                writeAll("~");
                writeAll(shortened.suffix);
                if (idx != selected) writeAll(RESET);
            } else if (findSpecialPrefix(path)) |prefix_len| {
                if (idx != selected) writeAll(BLUE);
                writeAll(path[0..prefix_len]);
                if (idx != selected) writeAll(RESET);
                writeAll(path[prefix_len..]);
            } else {
                writeAll(path);
            }

            writeFmt(DIM ++ " ({d})" ++ RESET, .{info.count});
            if (idx == selected) {
                writeAll(RESET);
            }
        }
        writeAll("\r\n");
    }

    // Status line
    writeAll(CLEAR_LINE);
    writeFmt(DIM ++ " [{d}/{d}] \xe2\x86\x91\xe2\x86\x93/jk: navigate  \xe2\x86\xb5: ls -al  q: quit" ++ RESET, .{ selected + 1, paths.len });
}

fn runLs(path: []const u8, io: Io) void {
    writeAll(CLEAR_SCREEN ++ CURSOR_HOME ++ SHOW_CURSOR);

    var cmd_buf: [4096]u8 = undefined;
    const cmd = std.fmt.bufPrint(&cmd_buf, "ls -al '{s}' | less", .{path}) catch return;

    var child = std.process.spawn(io, .{
        .argv = &.{ "sh", "-c", cmd },
    }) catch return;
    _ = child.wait(io) catch {};
}

fn interactiveMode(paths: []const []const u8, home: []const u8, io: Io) void {
    if (paths.len == 0) {
        writeAll("No paths found in PATH.\n");
        return;
    }

    const term_height = detectTerminalHeight();
    const visible_count: usize = @min(paths.len, @as(usize, term_height) -| 2);

    const orig_termios = enableRawMode();
    defer disableRawMode(orig_termios);
    defer writeAll(SHOW_CURSOR ++ CLEAR_SCREEN ++ CURSOR_HOME);

    writeAll(HIDE_CURSOR ++ CLEAR_SCREEN);

    var selected: usize = 0;
    var scroll_offset: usize = 0;

    while (true) {
        renderList(paths, home, selected, scroll_offset, visible_count, io);

        switch (readKey()) {
            .up => {
                if (selected > 0) {
                    selected -= 1;
                    if (selected < scroll_offset) {
                        scroll_offset = selected;
                    }
                }
            },
            .down => {
                if (selected + 1 < paths.len) {
                    selected += 1;
                    if (selected >= scroll_offset + visible_count) {
                        scroll_offset = selected - visible_count + 1;
                    }
                }
            },
            .enter => {
                disableRawMode(orig_termios);
                runLs(paths[selected], io);
                _ = enableRawMode();
                writeAll(HIDE_CURSOR ++ CLEAR_SCREEN);
            },
            .quit => return,
            .other => {},
        }
    }
}

fn collectPaths(gpa: std.mem.Allocator, path_env: []const u8) !std.ArrayList([]const u8) {
    var paths: std.ArrayList([]const u8) = .empty;
    var seen = std.StringHashMap(void).init(gpa);
    defer seen.deinit();

    var iter = std.mem.splitScalar(u8, path_env, ':');
    while (iter.next()) |dir_path| {
        if (dir_path.len == 0) continue;
        const result = seen.getOrPut(dir_path) catch continue;
        if (result.found_existing) continue;
        try paths.append(gpa, dir_path);
    }
    return paths;
}

pub fn main(init: std.process.Init) !void {
    const env = init.environ_map;
    const home = env.get("HOME") orelse "";
    const path_env = env.get("PATH") orelse "";

    const io = init.io;
    const gpa = init.gpa;

    // Check for -i flag
    var interactive = false;
    var args_iter = std.process.Args.Iterator.init(init.minimal.args);
    _ = args_iter.skip(); // skip program name
    while (args_iter.next()) |arg| {
        if (std.mem.eql(u8, arg, "-i")) {
            interactive = true;
            break;
        }
    }

    if (interactive) {
        var paths = try collectPaths(gpa, path_env);
        defer paths.deinit(gpa);
        interactiveMode(paths.items, home, io);
        return;
    }

    var stdout_buffer: [4096]u8 = undefined;
    var stdout_file_writer: Io.File.Writer = .init(.stdout(), io, &stdout_buffer);
    const w = &stdout_file_writer.interface;

    var seen = std.StringHashMap(void).init(gpa);
    defer seen.deinit();

    var iter = std.mem.splitScalar(u8, path_env, ':');
    while (iter.next()) |dir_path| {
        if (dir_path.len == 0) continue;
        const result = seen.getOrPut(dir_path) catch continue;
        if (result.found_existing) continue;
        try printEntry(w, io, dir_path, home);
    }

    try w.flush();
}

test "findSpecialPrefix detects known prefixes" {
    try std.testing.expectEqual(@as(?usize, 13), findSpecialPrefix("/opt/homebrew/bin"));
    try std.testing.expectEqual(@as(?usize, 13), findSpecialPrefix("/opt/homebrew/sbin"));
    try std.testing.expectEqual(@as(?usize, 13), findSpecialPrefix("/opt/homebrew"));
    try std.testing.expectEqual(@as(?usize, 13), findSpecialPrefix("/opt/workbrew/bin"));
    try std.testing.expectEqual(@as(?usize, 13), findSpecialPrefix("/opt/zerobrew/prefix/bin"));
}

test "findSpecialPrefix rejects non-matching paths" {
    try std.testing.expectEqual(@as(?usize, null), findSpecialPrefix("/usr/bin"));
    try std.testing.expectEqual(@as(?usize, null), findSpecialPrefix("/opt/homebrewery"));
    try std.testing.expectEqual(@as(?usize, null), findSpecialPrefix("/opt/homebrew2/bin"));
    try std.testing.expectEqual(@as(?usize, null), findSpecialPrefix(""));
    try std.testing.expectEqual(@as(?usize, null), findSpecialPrefix("/opt/pmk/env/global/bin"));
}

test "shortenHome replaces home prefix with suffix" {
    const home = "/Users/test";
    {
        const r = shortenHome("/Users/test/bin", home);
        try std.testing.expect(r.is_home);
        try std.testing.expectEqualStrings("/bin", r.suffix);
    }
    {
        const r = shortenHome("/Users/test", home);
        try std.testing.expect(r.is_home);
        try std.testing.expectEqualStrings("", r.suffix);
    }
}

test "shortenHome does not match partial home" {
    const home = "/Users/test";
    {
        const r = shortenHome("/Users/testing/bin", home);
        try std.testing.expect(!r.is_home);
        try std.testing.expectEqualStrings("/Users/testing/bin", r.suffix);
    }
    {
        const r = shortenHome("/usr/bin", home);
        try std.testing.expect(!r.is_home);
        try std.testing.expectEqualStrings("/usr/bin", r.suffix);
    }
}
