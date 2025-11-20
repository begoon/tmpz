const std = @import("std");

const VENDOR_PREFIX = "vendor/python-wsq/";

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "wsq",
        .root_module = b.createModule(.{
            .target = target,
            .optimize = optimize,
        }),
    });

    const c_files = [_][]const u8{
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/ioutil/dataio.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/ioutil/filesize.c",

        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/bres.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/bubble.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/computil.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/fatalerr.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/invbyte.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/invbytes.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/memalloc.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/ssxstats.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/syserr.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/ticks.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/util/time.c",

        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/allocfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/delfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/extrfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/freefet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/lkupfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/nistcom.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/printfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/readfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/strfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/updatfet.c",
        VENDOR_PREFIX ++ "csrc/commonnbis/src/lib/fet/writefet.c",

        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/cropcoeff.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/decoder.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/encoder.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/globals.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/huff.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/ppi.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/sd14util.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/tableio.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/tree.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/wsq/util.c",

        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/decoder.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/encoder.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/huff.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/huftable.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/imgdat.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/ppi.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/sd4util.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/tableio.c",
        VENDOR_PREFIX ++ "csrc/imgtools/src/lib/jpegl/util.c",

        "main.c",
    };

    const cflags = [_][]const u8{
        "-D_POSIX_SOURCE",
        "-D__NBISLE__",
        "-D__NBIS_PNG__",
        "-m64",
    };

    exe.addCSourceFiles(.{
        .files = &c_files,
        .flags = &cflags,
    });

    const include_dirs = [_][]const u8{
        VENDOR_PREFIX ++ "csrc/commonnbis/include",
        VENDOR_PREFIX ++ "csrc/imgtools/include",
        "csrc",
    };

    for (include_dirs) |dir| {
        exe.addIncludePath(b.path(dir));
    }

    exe.linkLibC();

    b.installArtifact(exe);
}
