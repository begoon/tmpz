const std = @import("std");

fn second() !void {
    std.debug.print("inside function(), now returning an error!\n", .{});
    return error.JumpBack;
}

fn first() !void {
    std.debug.print("inside function(), calling function()\n", .{});
    try second();
}

pub fn main() void {
    std.debug.print("calling function()\n", .{});

    first() catch |err| {
        std.debug.print("Back in main() after catching the error {any}!\n", .{err});
    };

    std.debug.print("Program continues normally...\n", .{});
}
