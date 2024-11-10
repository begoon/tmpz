const std = @import("std");
const json = std.json;
const Allocator = std.mem.Allocator;
const print = std.debug.print;

fn firstLine(buf: []const u8) ![]const u8 {
    var i: usize = 0;
    while (i < buf.len and buf[i] != '\n') : (i += 1) {}

    if (i == buf.len) return error.IncompleteHTTPRequest;

    return buf[0..i];
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    const addr = std.net.Address.initIp4(.{ 0, 0, 0, 0 }, 8000);
    var listener = try addr.listen(.{});

    print("listening on port 8000\n", .{});

    while (true) {
        const client = try listener.accept();
        defer client.stream.close();

        var buf = try allocator.alloc(u8, 1024);
        defer allocator.free(buf);

        const len = try client.stream.read(buf);
        const request = buf[0..len];
        const first = try firstLine(request);

        print("REQUEST: {s}\n", .{first});

        if (std.mem.startsWith(u8, first, "GET /version")) {
            try handleVersion(client.stream);
        } else {
            try client.stream.writer().writeAll("HTTP/1.1 404 Not Found\r\n\r\n");
        }

        print("RESPONSE SENT\n", .{});
    }
}

fn handleVersion(client: std.net.Stream) !void {
    const version = struct { status: []const u8, version: []const u8 }{
        .status = "alive",
        .version = "1.0.0",
    };

    var buffer: [1024]u8 = undefined;
    var stream = std.io.fixedBufferStream(&buffer);
    try json.stringify(version, .{}, stream.writer());
    const response = stream.getWritten();

    try client.writer().writeAll("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n");
    try client.writer().writeAll(response);
}
