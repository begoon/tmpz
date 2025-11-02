const std = @import("std");

extern "env" fn print(ptr: i32, len: i32) void;

fn print_slice(s: []const u8) void {
    const ptr: i32 = @intCast(@intFromPtr(s.ptr));
    const len: i32 = @intCast(s.len);
    print(ptr, len);
}

// Print u64 as 16-digit hex with 0x prefix (no allocation)
pub export fn print_u64_hex(x: u64) void {
    // "0x" + 16 hex digits = 18 bytes
    var buf: [18]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, "0x{x:0>16}", .{x}) catch unreachable;
    print_slice(s);
}

// Print u64 as decimal (no allocation)
pub export fn print_u64_dec(x: u64) void {
    // max u64 is 20 decimal digits
    var buf: [20]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, "{d}", .{x}) catch unreachable;
    print_slice(s);
}

// Your existing function (example usage)
pub export fn func(w: i32, a: u64, b: u64) u64 {
    const msg: []const u8 = "func() called";
    print_slice(msg);

    // Example: also print the chosen value in hex
    const chosen = if (w == 0) a else b;
    print_u64_hex(chosen);
    print_u64_dec(chosen);

    return chosen;
}
