const std = @import("std");
const testing = std.testing;

test "benchmark" {
    var timer = try std.time.Timer.start();
    var sum: u64 = 0;
    for (0..10_000_000) |i| {
        sum += i;
    }
    const seconds: f64 = @as(f64, @floatFromInt(timer.read())) / std.time.ns_per_s;
    std.debug.print("elapsed: {} seconds\n", .{seconds});
    try testing.expect(sum > 0);
}
