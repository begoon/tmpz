const std = @import("std");
const runner = @import("runner");
const zero_native = @import("zero-native");

pub const panic = std.debug.FullPanic(zero_native.debug.capturePanic);

const dev_origins = [_][]const u8{ "zero://app", "zero://inline", "http://127.0.0.1:5173" };

const App = struct {
    env_map: *std.process.Environ.Map,
    counter: i32 = 0,

    fn app(self: *@This()) zero_native.App {
        return .{
            .context = self,
            .name = "trial",
            .source = zero_native.frontend.productionSource(.{ .dist = "frontend/dist" }),
            .source_fn = source,
        };
    }

    fn source(context: *anyopaque) anyerror!zero_native.WebViewSource {
        const self: *@This() = @ptrCast(@alignCast(context));
        return zero_native.frontend.sourceFromEnv(self.env_map, .{
            .dist = "frontend/dist",
            .entry = "index.html",
        });
    }

    fn handleSystemInfo(context: *anyopaque, invocation: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        _ = context;
        _ = invocation;
        const uts = std.posix.uname();
        const sysname = std.mem.sliceTo(&uts.sysname, 0);
        const nodename = std.mem.sliceTo(&uts.nodename, 0);
        const release = std.mem.sliceTo(&uts.release, 0);
        const machine = std.mem.sliceTo(&uts.machine, 0);
        const cpus = std.Thread.getCpuCount() catch 0;
        var writer = std.Io.Writer.fixed(output);
        try writer.print(
            "{{\"sysname\":\"{s}\",\"nodename\":\"{s}\",\"release\":\"{s}\",\"machine\":\"{s}\",\"cpus\":{d}}}",
            .{ sysname, nodename, release, machine, cpus },
        );
        return writer.buffered();
    }

    fn handleCounterGet(context: *anyopaque, invocation: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        const self: *@This() = @ptrCast(@alignCast(context));
        _ = invocation;
        var writer = std.Io.Writer.fixed(output);
        try writer.print("{{\"value\":{d}}}", .{self.counter});
        return writer.buffered();
    }

    fn handleCounterIncrement(context: *anyopaque, invocation: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        const self: *@This() = @ptrCast(@alignCast(context));
        _ = invocation;
        self.counter +%= 1;
        var writer = std.Io.Writer.fixed(output);
        try writer.print("{{\"value\":{d}}}", .{self.counter});
        return writer.buffered();
    }

    fn handleCounterReset(context: *anyopaque, invocation: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        const self: *@This() = @ptrCast(@alignCast(context));
        _ = invocation;
        _ = output;
        self.counter = 0;
        return "{\"value\":0}";
    }
};

const command_policies = [_]zero_native.BridgeCommandPolicy{
    .{ .name = "system.info", .origins = &dev_origins },
    .{ .name = "counter.get", .origins = &dev_origins },
    .{ .name = "counter.increment", .origins = &dev_origins },
    .{ .name = "counter.reset", .origins = &dev_origins },
};

pub fn main(init: std.process.Init) !void {
    var app = App{ .env_map = init.environ_map };

    const handlers = [_]zero_native.BridgeHandler{
        .{ .name = "system.info", .context = &app, .invoke_fn = App.handleSystemInfo },
        .{ .name = "counter.get", .context = &app, .invoke_fn = App.handleCounterGet },
        .{ .name = "counter.increment", .context = &app, .invoke_fn = App.handleCounterIncrement },
        .{ .name = "counter.reset", .context = &app, .invoke_fn = App.handleCounterReset },
    };

    const dispatcher = zero_native.BridgeDispatcher{
        .policy = .{ .enabled = true, .commands = &command_policies },
        .registry = .{ .handlers = &handlers },
    };

    try runner.runWithOptions(app.app(), .{
        .app_name = "Trial",
        .window_title = "Trial",
        .bundle_id = "dev.zero_native.trial",
        .icon_path = "assets/icon.icns",
        .bridge = dispatcher,
        .security = .{ .navigation = .{ .allowed_origins = &dev_origins } },
    }, init);
}

test "app name is configured" {
    try std.testing.expectEqualStrings("trial", "trial");
}
