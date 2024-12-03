const std = @import("std");

const metaURL = "http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip";
const ipURL = "https://api.ipify.org";

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var client = std.http.Client{ .allocator = allocator };
    defer client.deinit();

    var url: []const u8 = undefined;
    if (std.posix.getenv("X") == null) {
        url = metaURL;
    } else {
        url = ipURL;
    }

    const uri = try std.Uri.parse(url);
    const headers = [_]std.http.Header{std.http.Header{
        .name = "Metadata-Flavor",
        .value = "Google",
    }};

    var buf: [4096]u8 = undefined;
    var request = client.open(.GET, uri, .{
        .server_header_buffer = &buf,
        .extra_headers = &headers,
    }) catch |err| {
        std.debug.print("{any}: {any}\n", .{ err, uri });
        return;
    };
    defer request.deinit();

    try request.send();
    try request.finish();
    try request.wait();

    if (request.response.status != .ok) {
        std.debug.print("error: {d}\n", .{request.response.status});
        return;
    }

    const sz = try request.readAll(&buf);
    const data = buf[0..sz];
    std.debug.print("{s}\n", .{data});
}
