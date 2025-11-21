const std = @import("std");

const VENDOR_PREFIX = "vendor/python-wsq/";

fn collectCFiles(b: *std.Build, dirs: []const []const u8) []const []const u8 {
    var list = std.ArrayList([]const u8){};
    const allocator = b.allocator;
    const cwd = std.fs.cwd();

    for (dirs) |dir_path| {
        var dir = cwd.openDir(dir_path, .{ .iterate = true }) catch unreachable;
        defer dir.close();

        var it = dir.iterate();
        while (true) {
            const next = it.next() catch unreachable;
            if (next == null) break;

            const entry = next.?;
            if (entry.kind != .file) continue;
            if (!std.mem.endsWith(u8, entry.name, ".c")) continue;

            const full_path =
                std.fs.path.join(allocator, &.{ dir_path, entry.name }) catch unreachable;

            list.append(allocator, full_path) catch unreachable;
        }
    }

    return list.items;
}

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "wsq",
        .root_module = b.createModule(.{
            .root_source_file = b.path("main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    // Directories where *all* .c files should be compiled
    const c_dirs = [_][]const u8{
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/ioutil",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl",
    };

    const c_files = collectCFiles(b, &c_dirs);

    const cflags = [_][]const u8{
        "-D_POSIX_SOURCE",
        "-D__NBISLE__",
        "-D__NBIS_PNG__",
        "-m64",
    };

    exe.addCSourceFiles(.{
        .files = c_files,
        .flags = &cflags,
    });

    const include_dirs = [_][]const u8{
        VENDOR_PREFIX ++ "csrc/commonnbis/include",
        VENDOR_PREFIX ++ "csrc/imgtools/include",
        VENDOR_PREFIX ++ "csrc",
    };

    for (include_dirs) |dir| {
        exe.addIncludePath(b.path(dir));
    }

    exe.linkLibC();

    b.installArtifact(exe);
}
