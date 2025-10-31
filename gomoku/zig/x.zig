const std = @import("std");

const allocator = std.heap.page_allocator;

fn a(array: *[NN]i8) []i8 {
    array[2] = 100;
    return array[1..4];
}

const NN = 256;

pub fn main() void {
    var array: [NN]i8 = .{0} ** NN;
    std.debug.print("array {any} {} {*}!\n", .{ array, array.len, &array });
    const v = a(&array);
    std.debug.print("array {any} {} {*}!\n", .{ v, v.len, v.ptr });
    var c: u8 = 'A';
    c = c + 1;
    std.debug.print("char: {c}\n", .{c});
    // -----------

    var backing: [5][16]u8 = undefined;
    const strings = make_strings(&backing);

    std.debug.print("{} {} [{s}|{s}]\n", .{ @TypeOf(strings), strings.len, strings[0], strings[1] }-);
}

fn make_strings(v: *[5][]u8) [][16]u8 {
    @memcpy(&v[0], "1234567890ABCDEF");
    v[1][0] = '$';
    return v[0..2];
}
