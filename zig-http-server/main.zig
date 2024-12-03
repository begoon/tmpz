const std = @import("std");

const httpz = @import("httpz");

const Logger = @import("middleware/logger.zig");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    const allocator = gpa.allocator();

    var handler = Handler{};
    var server = try httpz.Server(*Handler).init(allocator, .{ .port = 8000 }, &handler);
    defer {
        server.stop();
        server.deinit();
    }

    const logger = try server.middleware(Logger, .{ .query = true });

    var router = server.router(.{});
    router.middlewares = &.{logger};

    router.get("/", indexHandler, .{});
    router.get("/info", infoHandler, .{});
    router.get("/user/:id", userHandler, .{});
    router.get("/version", versionHandler, .{});
    router.get("/pause/:n", pauseHandler, .{});
    router.get("/error", @"error", .{});
    router.get("/counter", counter, .{});

    std.debug.print("listening on port 8000\n", .{});
    // blocks
    try server.listen();
}

const Handler = struct {
    _counter: usize = 0,

    pub fn notFound(_: *Handler, _: *httpz.Request, res: *httpz.Response) !void {
        res.status = 404;
        res.body = "ha?";
    }

    pub fn uncaughtError(_: *Handler, req: *httpz.Request, res: *httpz.Response, err: anyerror) void {
        std.debug.print("uncaught http error at {s}: {}\n", .{ req.url.path, err });
        res.headers.add("content-type", "text/html; charset=utf-8");
        res.status = 505;
        res.body = "BOOM!";
    }

    pub fn dispatch(self: *Handler, action: httpz.Action(*Handler), req: *httpz.Request, res: *httpz.Response) !void {
        var start = try std.time.Timer.start();
        try action(self, req, res);
        std.debug.print("ts={d} us={d} path={s}\n", .{ std.time.timestamp(), start.lap() / 1000, req.url.path });
    }
};

const indexHTML = @embedFile("index.html");

fn indexHandler(_: *Handler, _: *httpz.Request, res: *httpz.Response) !void {
    res.status = 200;
    res.content_type = .HTML;
    try res.writer().writeAll(indexHTML);
}

fn infoHandler(_: *Handler, _: *httpz.Request, res: *httpz.Response) !void {
    res.status = 200;
    res.content_type = .HTML;
    res.body =
        \\<p>
        \\There's overlap between a custom dispatch function and middlewares.
        \\has no middleware, effectively disabling the Logger for that route.
        \\</p>
    ;
}
fn pauseHandler(_: *Handler, req: *httpz.Request, res: *httpz.Response) !void {
    const n = req.param("n").?;
    const seconds = try std.fmt.parseInt(u64, n, 10);
    std.log.info("pause for {d} seconds", .{seconds});
    const ns = std.time.ns_per_s * seconds;
    std.time.sleep(ns);
    res.status = 200;
    try res.json(.{ .seconds = seconds, .ns = ns }, .{});
}

fn userHandler(_: *Handler, req: *httpz.Request, res: *httpz.Response) !void {
    res.status = 200;
    try res.json(.{ .id = req.param("id").?, .name = "NAME" }, .{});
}

fn versionHandler(_: *Handler, req: *httpz.Request, res: *httpz.Response) !void {
    std.log.info("{any} {s}", .{ req.method, req.url.path });
    res.status = 200;
    try res.json(.{ .version = "0.0.1" }, .{});
}

pub fn counter(h: *Handler, _: *httpz.Request, res: *httpz.Response) !void {
    const value = @atomicRmw(usize, &h._counter, .Add, 1, .monotonic);
    return res.json(.{ .counter = value + 1 }, .{});
}

fn @"error"(_: *Handler, _: *httpz.Request, _: *httpz.Response) !void {
    return error.ActionError;
}

test "test number" {
    var list = std.ArrayList(i32).init(std.testing.allocator);
    defer list.deinit();
    try list.append(40);
    try std.testing.expectEqual(@as(i32, 40), list.pop());
}

test "test index" {
    try std.testing.expectEqual(indexHTML, "INDEX\n");
}
