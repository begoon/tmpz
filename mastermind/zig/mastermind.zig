const std = @import("std");

const Comparison = struct {
    in_place: i32,
    by_value: i32,
};

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const universe = try createUniverse(allocator);
    defer allocator.free(universe);

    var candidates = try createUniverse(allocator);
    defer allocator.free(candidates);

    var tries: i32 = 1;

    while (true) {
        // Knuth minimax probe selection
        var best_probe: u32 = 0;
        var min_rank: u32 = 0;

        for (universe) |probe| {
            var probe_in_candidates: u32 = 0;

            var buckets: [45]u32 = [_]u32{0} ** 45; // index = in_place*10 + by_value
            var worst_eval: u32 = 0;

            for (candidates) |candidate| {
                if (probe == candidate) {
                    probe_in_candidates = 1;
                }

                if (candidate == 0) continue; // eliminated
                const cmp = compare(probe, candidate);
                const valuation: usize = @intCast(cmp.in_place * 10 + cmp.by_value);
                buckets[valuation] += 1;
                if (buckets[valuation] > worst_eval) worst_eval = buckets[valuation];
            }

            // rank = probe (1111..6666) + (not in candidates)*10000 + worst_eval*100000
            const rank: u32 = probe + (1 - probe_in_candidates) * 10000 + worst_eval * 100000;
            if (min_rank == 0 or rank < min_rank) {
                min_rank = rank;
                best_probe = probe;
            }
        }

        std.debug.print("\nmaybe {d} ? \n", .{best_probe});
        std.debug.print("#{d}, enter feedback, <in-place> and <by-value> (e.g. \"1 2\"):\n", .{tries});

        var in_place: i32 = 0;
        var by_value: i32 = 0;

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

        if (in_place == 4) {
            std.debug.print("\nguesses in {d} tries\n", .{tries});
            break;
        }

        var eliminated: i32 = 0;
        var remaining: i32 = 0;

        std.debug.print("\n", .{});

        // eliminate candidates not matching feedback
        for (candidates, 0..) |candidate, i| {
            if (candidate == 0) continue; // already eliminated
            const cmp = compare(best_probe, candidate);
            if (cmp.in_place != in_place or cmp.by_value != by_value) {
                candidates[i] = 0;
                eliminated += 1;
            } else {
                remaining += 1;
                std.debug.print("{d} ", .{candidate});
            }
        }
        std.debug.print("\n{d} candidates eliminated, {d} remaining\n", .{ eliminated, remaining });

        if (remaining == 0) {
            std.debug.print("no candidates remaining, it is impossible!\n", .{});
            break;
        }

        tries += 1;
    }
}

/// build the universe: integers 1111..6666 with base-6 digits (1..6)
fn createUniverse(allocator: std.mem.Allocator) ![]u32 {
    const N: usize = 6 * 6 * 6 * 6; // 1296
    var universe = try allocator.alloc(u32, N);

    var off: usize = 0;
    var i: u32 = 0;
    while (i < 6) : (i += 1) {
        var j: u32 = 0;
        while (j < 6) : (j += 1) {
            var k: u32 = 0;
            while (k < 6) : (k += 1) {
                var l: u32 = 0;
                while (l < 6) : (l += 1) {
                    const v: u32 = i * 1000 + j * 100 + k * 10 + l + 1111;
                    universe[off] = v;
                    off += 1;
                }
            }
        }
    }
    return universe;
}

/// compare a probe against a code, returning <in_place, by_value>
fn compare(probe: u32, code: u32) Comparison {
    const p = [_]u32{
        (probe / 1000) % 10,
        (probe / 100) % 10,
        (probe / 10) % 10,
        probe % 10,
    };
    const c = [_]u32{
        (code / 1000) % 10,
        (code / 100) % 10,
        (code / 10) % 10,
        code % 10,
    };

    var in_place: i32 = 0;
    var by_value: i32 = 0;

    // digits are 1..6; use small freq table [0..9] just in case
    var freq: [10]i32 = [_]i32{0} ** 10;

    // pass 1: in-place matches and build frequencies for others
    var i: usize = 0;
    while (i < 4) : (i += 1) {
        if (p[i] == c[i]) {
            in_place += 1;
        } else {
            const cv = c[i];
            if (cv >= 0 and cv < 10) freq[cv] += 1;
        }
    }

    // pass 2: by-value matches using remaining frequencies
    i = 0;
    while (i < 4) : (i += 1) {
        if (p[i] == c[i]) continue; // already counted in-place
        const pv = p[i];
        if (pv >= 0 and pv < 10 and freq[pv] > 0) {
            by_value += 1;
            freq[pv] -= 1;
        }
    }

    return .{ .in_place = in_place, .by_value = by_value };
}

fn readInput(reader: *std.Io.Reader) !Comparison {
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

test "compare" {
    const tests = [_][4]u32{
        [4]u32{ 1234, 1234, 4, 0 },
        [4]u32{ 1234, 4321, 0, 4 },
        [4]u32{ 1234, 1111, 1, 0 },
        [4]u32{ 1234, 2111, 0, 2 },
    };
    for (tests) |t| {
        const expected = Comparison{ .in_place = @intCast(t[2]), .by_value = @intCast(t[3]) };
        const result = compare(t[0], t[1]);
        try std.testing.expect(expected.in_place == result.in_place);
        try std.testing.expect(expected.by_value == result.by_value);
    }
}
