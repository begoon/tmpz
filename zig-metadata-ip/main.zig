const std = @import("std");

const metaURL = "http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip";
const ipURL = "https://api.ipify.org";

fn print_external_ip(allocator: std.mem.Allocator, uri: std.Uri) !void {
    const headers = [_]std.http.Header{std.http.Header{
        .name = "Metadata-Flavor",
        .value = "Google",
    }};

    var client = std.http.Client{ .allocator = allocator };
    defer client.deinit();

    var response_buf = std.ArrayList(u8).init(allocator);
    defer response_buf.deinit();

    const result = client.fetch(.{
        .location = .{ .uri = uri },
        .extra_headers = &headers,
        .response_storage = .{ .dynamic = &response_buf },
    }) catch |err| {
        std.debug.print("{any}: {any}\n", .{ err, uri });
        return err;
    };

    if (result.status != .ok) {
        std.debug.print("error: {d}\n", .{result.status});
        return;
    }
    std.debug.print("{s}\n", .{response_buf.items});
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var uri = try std.Uri.parse(metaURL);
    print_external_ip(allocator, uri) catch {
        uri = try std.Uri.parse(ipURL);
        try print_external_ip(allocator, uri);
    };
}
