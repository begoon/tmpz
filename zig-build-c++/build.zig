const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Root module for a pure C/C++ program
    const mod = b.createModule(.{
        .target = target,
        .optimize = optimize,
    });

    // Add your C++ source (add flags like "-std=c++20" if desired)
    mod.addCSourceFile(.{
        .file = b.path("src/hello.cpp"),
        .flags = &.{}, // e.g. &.{"-std=c++17"}
    });

    const exe = b.addExecutable(.{
        .name = "hello",
        .root_module = mod,
    });

    exe.linkLibC();
    exe.linkLibCpp();

    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    if (b.args) |args| run_cmd.addArgs(args);
    b.step("run", "Run the executable").dependOn(&run_cmd.step);
}
