const std = @import("std");
const httpz = @import("httpz");

const Logger = @This();

query: bool,

pub fn init(config: Config) !Logger {
    return .{
        .query = config.query,
    };
}

pub fn execute(self: *const Logger, req: *httpz.Request, res: *httpz.Response, executor: anytype) !void {
    const start = std.time.microTimestamp();
    defer {
        const elapsed = std.time.microTimestamp() - start;
        std.log.info("{d}\t{s}?{s}\t{d}\t{d}us", .{ start, req.url.path, if (self.query) req.url.query else "", res.status, elapsed });
    }
    return executor.next();
}

pub const Config = struct {
    query: bool,
};
