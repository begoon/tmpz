const std = @import("std");

const httpz = @import("httpz");

pub const std_options: std.Options = .{
    .log_level = .info,
};

const BRIGHT_WHITE = "\x1b[1;37m";
const BRIGHT_BLUE = "\x1b[1;34m";
const BRIGHT_GREEN = "\x1b[1;32m";
const BRIGHT_RED = "\x1b[1;31m";
const RESET = "\x1b[0m";

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();

    var server = try httpz.Server(void).init(allocator, .{ .port = 8000 }, {});

    const server_thread = try std.Thread.spawn(.{}, serverWorker, .{&server});

    defer {
        server.stop();
        server_thread.join();

        std.log.debug("done", .{});
        server.deinit();
    }

    // ---

    var client = std.http.Client{ .allocator = allocator };
    defer client.deinit();

    var response = std.ArrayList(u8).init(allocator);
    defer response.deinit();

    const uri = try std.Uri.parse("http://localhost:8000/");
    const result = client.fetch(.{
        .location = .{ .uri = uri },
        .response_storage = .{ .dynamic = &response },
    }) catch |err| {
        std.debug.print("{any}: {any}\n", .{ err, uri });
        return err;
    };

    if (result.status != .ok) {
        const phrase = result.status.phrase() orelse "unknown";
        std.log.err("unexpected status {d} {s}", .{ @intFromEnum(result.status), phrase });
        return;
    }
    std.debug.print("{s}{s}{s}\n", .{ BRIGHT_WHITE, response.items, RESET });
}

fn serverWorker(server: *httpz.Server(void)) !void {
    var router = server.router(.{});
    router.get("/", handler, .{});

    std.log.debug("listening on port 8000", .{});

    try server.listen();
    std.log.debug("server stopped", .{});
}

fn handler(req: *httpz.Request, res: *httpz.Response) !void {
    std.log.debug("{s} {s}", .{ @tagName(req.method), req.url.path });
    try res.chunk("Hello, World!");
}
