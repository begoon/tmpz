const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "zig-git-commit-embed",
        .root_source_file = b.path("main.zig"),
        .target = target,
        .optimize = optimize,
    });

    const sha = b.option([]const u8, "git-commit", "git commit") orelse "undefined";

    const options = b.addOptions();
    options.addOption([]const u8, "commit", sha);

    exe.root_module.addOptions("build_info", options);

    b.installArtifact(exe);
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());

    if (b.args) |args| {
        run_cmd.addArgs(args);
    }

    const run_step = b.step("run", "run");
    run_step.dependOn(&run_cmd.step);
}
