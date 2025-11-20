const std = @import("std");

// Import the C WSQ API.
const c = @cImport({
    @cInclude("wsq.h"); // your NBIS header
    @cInclude("stdlib.h"); // for free()
});

// NBIS tools expect a global `int debug` symbol.
pub export var debug: c_int = 0;

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const args = try std.process.argsAlloc(allocator);
    defer std.process.argsFree(allocator, args);

    var stderr_buffer: [1024]u8 = undefined;
    var stderr_state = std.fs.File.stderr().writer(&stderr_buffer);
    const stderr = &stderr_state.interface;

    if (args.len != 3) {
        try stderr.print("Usage: {s} input.wsq output.ppm\n", .{args[0]});
        std.process.exit(1);
    }

    const input_path = args[1];
    const output_path = args[2];

    const in_file = try std.fs.cwd().openFile(input_path, .{});
    defer in_file.close();

    const wsq_buffer = try in_file.readToEndAlloc(allocator, std.math.maxInt(usize));
    defer allocator.free(wsq_buffer);

    var out_buffer: [*c]u8 = null;
    var out_cols: c_int = 0;
    var out_rows: c_int = 0;
    var out_depth: c_int = 0;
    var out_ppi: c_int = 0;
    var out_lossy_flag: c_int = 0;

    const ret = c.wsq_decode_mem(
        &out_buffer,
        &out_cols,
        &out_rows,
        &out_depth,
        &out_ppi,
        &out_lossy_flag,
        wsq_buffer.ptr, // input bytes
        @intCast(wsq_buffer.len), // input length
    );

    if (ret != 0) {
        try stderr.print("error: wsq_decode_mem failed with code {d}\n", .{ret});
        if (out_buffer != null) {
            c.free(out_buffer);
        }
        std.process.exit(1);
    }

    // `out_buffer` was allocated via C malloc; make sure we free it later.
    defer c.free(out_buffer);

    if (out_depth != 8) {
        try stderr.print(
            "unexpected depth {d} (expected 8-bit grayscale)\n",
            .{out_depth},
        );
        std.process.exit(1);
    }

    const out_file = try std.fs.cwd().createFile(output_path, .{
        .truncate = true,
        .read = false,
        .mode = 0o666,
    });
    defer out_file.close();

    var buf: [1024]u8 = undefined;
    var writer_state = out_file.writer(&buf);
    const writer = &writer_state.interface;

    try writer.print("P2\n", .{});
    try writer.print("{d} {d}\n", .{ out_cols, out_rows });
    try writer.print("255\n", .{});

    const num_pixels = @as(usize, @intCast(out_cols)) * @as(usize, @intCast(out_rows));

    const out_slice = out_buffer[0..num_pixels];

    var i: usize = 0;
    const width = @as(usize, @intCast(out_cols));
    while (i < num_pixels) : (i += 1) {
        const v: u8 = out_slice[i];
        try writer.print("{d:3}", .{v});
        const eol = if ((i + 1) % width == 0) "\n" else " ";
        try writer.writeAll(eol);
    }
    try writer.flush();
}
