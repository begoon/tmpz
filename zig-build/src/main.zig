const std = @import("std");

const zig_build = @import("zig_build");

pub fn main() !void {
    std.debug.print("all your {s} are belong to 69\n", .{"codebase"});
    try zig_build.bufferedPrint();

    const S = struct {
        a: i32,
        b: f32,
    };
    var s: S = .{ .a = 42, .b = 3.14 };
    std.debug.print("s.a = {}, s.b = {}\n", .{ s.a, s.b });

    const p: *S = @fieldParentPtr("b", &s.b);
    p.a = 1234;
    std.debug.print("s.a = {}\n", .{s.a});
}

test "simple test" {
    const gpa = std.testing.allocator;
    var list: std.ArrayList(i32) = .empty;
    defer list.deinit(gpa); // commenting this out line causes a memory leak
    try list.append(gpa, 42);
    try std.testing.expectEqual(@as(i32, 42), list.pop());
}

test "fuzz example" {
    const Context = struct {
        fn testOne(context: @This(), input: []const u8) anyerror!void {
            _ = context;
            // pass `--fuzz` to `zig build test` to find a failure
            try std.testing.expect(!std.mem.eql(u8, "canyoufindme", input));
        }
    };
    try std.testing.fuzz(Context{}, Context.testOne, .{});
}
