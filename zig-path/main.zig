const std = @import("std");
const Io = std.Io;

const special_prefixes = [_][]const u8{
    "/opt/homebrew",
    "/opt/workbrew",
    "/opt/zerobrew",
};

// ANSI escape codes
const RESET = "\x1b[0m";
const BLUE = "\x1b[34m";
const WHITE = "\x1b[97m";
const DIM = "\x1b[2m";
const STRIKE = "\x1b[9m";

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
        try writer.writeAll(WHITE ++ "~");
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

pub fn main(init: std.process.Init) !void {
    const env = init.environ_map;
    const home = env.get("HOME") orelse "";
    const path_env = env.get("PATH") orelse "";

    const io = init.io;
    const gpa = init.gpa;
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
