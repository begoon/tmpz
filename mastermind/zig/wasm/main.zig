const std = @import("std");

const mastermind = @import("mastermind.zig");

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    var game = try mastermind.Game.init(allocator);
    defer game.deinit(allocator);

    var in_place: i32 = -1;
    var by_value: i32 = -1;

    while (true) {
        if (in_place != -1 and by_value != -1) {
            std.debug.print("remaining: {d}, eliminated: {d}\n", .{ game.remaining, game.eliminated });
            for (game.candidates) |candidate| {
                if (candidate != 0) {
                    std.debug.print("{d} ", .{candidate});
                }
            }
            std.debug.print("\n", .{});
        }

        const probe = game.guess(in_place, by_value);
        if (probe == 0) {
            std.debug.print("game over in {d} tries\n", .{game.tries});
            break;
        }
        if (probe == -1) {
            std.debug.print("no candidates remaining, something went wrong\n", .{});
            break;
        }

        std.debug.print("\nmaybe {d} ? \n", .{probe});
        std.debug.print("# {d}, enter feedback, <in-place> and <by-value> (e.g. \"1 2\"): ", .{game.tries});

        var stdin_buf: [256]u8 = undefined;
        var stdin_reader = std.fs.File.stdin().reader(&stdin_buf);
        const reader = &stdin_reader.interface;

        while (true) {
            std.debug.print("> ", .{});
            std.debug.print("please enter two integers like \"2 1\"\n", .{});
            const input = try readInput(reader);
            in_place = input.in_place;
            by_value = input.by_value;
            if (in_place >= 0 and in_place <= 4 and by_value >= 0 and by_value <= 4 and in_place + by_value <= 4) {
                break;
            }
        }
    }
}

fn readInput(reader: *std.Io.Reader) !mastermind.Comparison {
    var buf: [128]u8 = undefined;
    var w = std.io.Writer.fixed(&buf);
    const sz = try reader.streamDelimiterLimit(&w, '\n', .unlimited);
    const line = buf[0..sz];

    const cleared = std.mem.trimRight(u8, line, "\n");
    var parts = std.mem.splitSequence(u8, cleared, " ");

    const first = try std.fmt.parseInt(i32, parts.first(), 10);
    const second = try std.fmt.parseInt(i32, parts.next().?, 10);
    return .{ .in_place = first, .by_value = second };
}
