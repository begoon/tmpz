const std = @import("std");

pub fn main() !void {
    std.debug.print("OK\n", .{});

    std.debug.print("std.os.environ: {s}\n", .{std.os.environ});
    for (std.os.environ) |env| {
        std.debug.print("- env: {s}\n", .{env});
    }

    std.debug.print("std.os.argv: {s}\n", .{std.os.argv});
    for (std.os.argv) |arg| {
        std.debug.print("- arg: {s}\n", .{arg});
    }

    var args = std.process.args();
    while (args.next()) |arg| {
        std.debug.print("- arg: {s}\n", .{arg});
    }
}
