const std = @import("std");

extern fn print(ptr: [*]const u8, len: usize) void;

export fn func() void {
    format("{s}/{d}", .{ "formatter", 123 });
}

fn format(comptime fmt: []const u8, args: anytype) void {
    var buffer: [10240]u8 = undefined;
    const v = std.fmt.bufPrint(&buffer, fmt, args) catch return;
    print(v.ptr, v.len);
}

pub fn main() void {
    func();
}
