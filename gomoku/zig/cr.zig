const std = @import("std");

pub fn enter() !void {
    var out_buf: [256]u8 = undefined;
    var out_writer = std.fs.File.stdout().writer(&out_buf);
    const out = &out_writer.interface;

    var in_buf: [64]u8 = undefined;
    var in_reader = std.fs.File.stdin().readerStreaming(&in_buf);
    const input = &in_reader.interface;

    try out.print("press enter to continue...\n", .{});
    while (true) {
        const b = input.takeByte() catch |err| switch (err) {
            error.EndOfStream => break,
            else => return err,
        };
        if (b == '\n') break;
    }

    try out.flush();
}

pub fn main() !void {
    try enter();
}
