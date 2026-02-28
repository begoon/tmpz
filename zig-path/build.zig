const std = @import("std");

const name = "paths";

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});

    const exe = b.addExecutable(.{
        .name = name,
        .root_module = b.createModule(.{
            .root_source_file = b.path("main.zig"),
            .target = target,
            .optimize = .ReleaseFast,
        }),
    });

    b.installArtifact(exe);

    if (b.graph.environ_map.get("HOMEBREW_FORMULA_PREFIX") == null) {
        const home = b.graph.environ_map.get("HOME") orelse @panic("HOME not set");
        const dest = b.fmt("{s}/bin/{s}", .{ home, name });
        const cp = b.addSystemCommand(&.{ "cp", "-f" });
        cp.addArtifactArg(exe);
        cp.addArg(dest);

        const echo = b.addSystemCommand(&.{ "echo", b.fmt("installing {s} to ~/bin/{s}", .{ name, name }) });
        echo.step.dependOn(&cp.step);
        b.getInstallStep().dependOn(&echo.step);
    }

    const run_step = b.step("run", "run the application");

    const run_cmd = b.addRunArtifact(exe);
    run_step.dependOn(&run_cmd.step);

    run_cmd.step.dependOn(b.getInstallStep());

    if (b.args) |args| {
        run_cmd.addArgs(args);
    }

    const exe_tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("main.zig"),
            .target = target,
            .optimize = .Debug,
        }),
    });

    const run_exe_tests = b.addRunArtifact(exe_tests);

    const test_step = b.step("test", "run tests");
    test_step.dependOn(&run_exe_tests.step);

    const clean = b.step("clean", "delete .zig-cache and zig-out");
    clean.dependOn(&b.addSystemCommand(&.{ "rm", "-rf", ".zig-cache", "zig-out" }).step);
}
