const std = @import("std");

pub fn main() !void {
    std.debug.print("[{}]\n", .{@typeInfo(u8)});
    std.debug.print("[{s}]\n", .{@typeName(u8)});

    const z: u8 = 0;
    const a: @TypeOf(z) = 100;
    std.debug.print("[{d}]\n", .{a});
}
