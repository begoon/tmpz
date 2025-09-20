const std = @import("std");

pub fn build(b: *std.Build) !void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "cli",
        .root_module = b.createModule(.{
            .target = target,
            .optimize = optimize,
        }),
    });

    var dir = try std.fs.cwd().openDir(".", .{ .iterate = true });
    defer dir.close();

    var it = dir.iterate();
    while (try it.next()) |entry| {
        if (entry.kind == .file and std.mem.endsWith(u8, entry.name, ".c")) {
            exe.addCSourceFile(.{
                .file = b.path(entry.name),
                .flags = &.{"-std=c23"},
            });
        }
    }

    exe.linkLibC();
    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    b.step("run", "Run the application").dependOn(&run_cmd.step);
}
