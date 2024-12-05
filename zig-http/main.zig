const std = @import("std");
const json = std.json;

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    if (std.os.argv.len < 2) {
        std.debug.print("usage: {s} <url>\n", .{std.os.argv[0]});
        return;
    }

    var client = std.http.Client{ .allocator = allocator };
    defer client.deinit();

    std.debug.print("argv: {s}\n", .{std.os.argv});

    const args = try std.process.argsAlloc(allocator);
    defer std.process.argsFree(allocator, args);
    std.debug.print("URL: {s}\n", .{args[1]});

    const uri = try std.Uri.parse(args[1]);
    std.debug.print("parsed URL: {}\n", .{uri});

    var buf: [4096]u8 = undefined;
    var request = try client.open(.GET, uri, .{ .server_header_buffer = &buf });
    defer request.deinit();

    try request.send();
    try request.finish();
    try request.wait();

    std.debug.print("status = {d}\n", .{request.response.status});

    var iter = request.response.iterateHeaders();
    while (iter.next()) |header| {
        std.debug.print("{s} = {s}\n", .{ header.name, header.value });
    }

    try std.testing.expectEqual(request.response.status, .ok);

    var reader = request.reader();
    const body = try reader.readAllAlloc(allocator, 1024 * 1024 * 4);
    defer allocator.free(body);

    std.debug.print("body:\n{s}\n", .{body});

    const IP = struct {
        origin: []const u8,
        // tag: []const u8, // = "?"
    };
    const ip = json.parseFromSlice(
        IP,
        allocator,
        body,
        .{ .ignore_unknown_fields = true },
    ) catch |err| {
        std.log.err("ip: {}", .{err});
        return;
    };
    defer ip.deinit();
    std.debug.print("ip: {}\n", .{ip});
    std.debug.print("origin: {s}\n", .{ip.value.origin});
}
