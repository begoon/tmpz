const std = @import("std");

pub fn main() !void {
    std.debug.print("hola!\n", .{});
    var t1 = try std.Thread.spawn(.{}, worker, .{123});
    std.debug.print("main/ok\n", .{});
    t1.join();
}

fn worker(a: u8) void {
    std.debug.print("BEFORE: {} worker\n", .{a});

    std.time.sleep(2 * std.time.ns_per_s);
    std.debug.print("worker\n", .{});

    std.debug.print("AFTER: worker\n", .{});
}
