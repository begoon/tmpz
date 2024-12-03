const std = @import("std");

const httpz = @import("httpz");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();

    var server = try httpz.Server(void).init(allocator, .{ .port = 8000 }, {});
    defer {
        server.stop();
        server.deinit();
    }

    var router = server.router(.{});
    router.get("/user/:id", userHandler, .{});
    router.get("/version", versionHandler, .{});

    std.debug.print("listening on port 8000\n", .{});
    // blocks
    try server.listen();
}

fn userHandler(req: *httpz.Request, res: *httpz.Response) !void {
    res.status = 200;
    try res.json(.{ .id = req.param("id").?, .name = "NAME" }, .{});
}

fn versionHandler(req: *httpz.Request, res: *httpz.Response) !void {
    std.log.info("{any} {s}", .{ req.method, req.url.path });
    res.status = 200;
    try res.json(.{ .version = "0.0.1" }, .{});
}
