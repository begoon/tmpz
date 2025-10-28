const std = @import("std");

pub const Comparison = struct {
    in_place: i32,
    by_value: i32,
};

pub const Game = struct {
    universe: []u32,
    candidates: []u32,
    probe: u32,
    tries: i32,
    eliminated: i32,
    remaining: i32,

    pub fn init(allocator: std.mem.Allocator) !Game {
        const universe = try createUniverse(allocator);
        const candidates = try createUniverse(allocator);
        return Game{
            .universe = universe,
            .candidates = candidates,
            .probe = 0,
            .tries = 0,
            .eliminated = 0,
            .remaining = @intCast(universe.len),
        };
    }

    pub fn deinit(self: *Game, allocator: std.mem.Allocator) void {
        allocator.free(self.universe);
        allocator.free(self.candidates);
    }

    pub fn reset(self: *Game, allocator: std.mem.Allocator) !void {
        allocator.free(self.candidates);
        self.candidates = try createUniverse(allocator);
        self.probe = 0;
        self.tries = 0;
        self.eliminated = 0;
        self.remaining = @intCast(self.universe.len);
    }

    pub fn guess(self: *Game, in_place: i32, by_value: i32) i32 {
        if (in_place == 4) {
            return 0;
        }

        if (self.probe != 0) {
            self.eliminate(self.probe, in_place, by_value);
        }

        if (self.remaining == 0) {
            return -1;
        }

        var best_probe: u32 = 0;
        var min_rank: u32 = 0;

        for (self.universe) |probe| {
            var probe_in_candidates: u32 = 0;

            var buckets: [45]u32 = [_]u32{0} ** 45; // index = in_place*10 + by_value
            var worst_eval: u32 = 0;

            for (self.candidates) |candidate| {
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

        self.probe = best_probe;

        self.tries += 1;
        return @intCast(best_probe);
    }

    fn eliminate(self: *Game, probe: u32, in_place: i32, by_value: i32) void {
        self.eliminated = 0;
        self.remaining = 0;

        // eliminate candidates not matching feedback
        for (self.candidates, 0..) |candidate, i| {
            if (candidate == 0) continue; // already eliminated
            const cmp = compare(probe, candidate);
            if (cmp.in_place != in_place or cmp.by_value != by_value) {
                self.candidates[i] = 0;
                self.eliminated += 1;
            } else {
                self.remaining += 1;
            }
        }
    }
};

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
