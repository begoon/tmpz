//! By convention, root.zig is the root source file when making a library. If
//! you are making an executable, the convention is to delete this file and
//! start with main.zig instead.
const std = @import("std");
const testing = std.testing;

pub export fn add(a: i32, b: i32) i32 {
    return a + b;
}

test "basic add functionality" {
    try testing.expect(add(3, 7) == 10);
}

pub fn subtract(a: i32, comptime b: anytype) i32 {
    const bb = switch (@TypeOf(b)) {
        i32 => @as(i32, b),
        u8 => @as(u32, b),
        else => @compileError("subtract expects an i32 as the second argument"),
    };
    return a - bb;
}

test "basic subtract functionality" {
    try testing.expect(subtract(10, @as(i32, 3)) == 7);
    try testing.expect(subtract(10, @as(u8, 3)) == 7);
}
