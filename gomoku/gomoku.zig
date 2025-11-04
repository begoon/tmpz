const std = @import("std");
const eql = std.mem.eql;
const testing = std.testing;
const builtin = @import("builtin");

const WASM = builtin.target.cpu.arch == .wasm32;

extern fn console(msg: [*]const u8, len: usize) void;
extern fn status(msg: [*]const u8, len: usize) void;
extern fn enter() void;

const DEPTH = 5;
const QDEPTH: i32 = 1; // tune 2..6 based on speed
const QUIET_THRESHOLD: i32 = 90; // ~ bigger than any 10/2/1 patterns, close to 100s
const ORDER_MOVES = true; // tune true/false based on speed

pub const N: i32 = 15;
pub const NN: usize = N * N;

// keep evaluation sensitive to shortest scored pattern (currently 3..6)
const MIN_EVAL_PATTERN_LEN: usize = 3;

pub const Field = enum {
    empty,
    human,
    computer,
};

inline fn player_index(player: Field) usize {
    return switch (player) {
        .human => 0,
        .computer => 1,
        else => unreachable,
    };
}

inline fn left_to_right_diagonal_index(r: i32, c: i32) usize {
    // r - c in [-(N-1) .. N-1]  => shift by (N-1)
    return @intCast(r - c + (N - 1));
}

inline fn left_to_right_diagonal_start(n: usize) Move {
    const offset: i32 = @as(i32, @intCast(n)) - (N - 1);
    const start_r: i32 = if (offset >= 0) offset else 0;
    const start_c: i32 = if (offset >= 0) 0 else -offset;
    return Move.at(start_r, start_c);
}

inline fn left_to_right_diagonal_length(i: usize) usize {
    const offset: i32 = @as(i32, @intCast(i)) - (N - 1); // r-c
    return @intCast(N - @as(i32, @intCast(@abs(offset)))); // length = N - |r-c|
}

inline fn right_to_left_diagonal_index(r: i32, c: i32) usize {
    // r + c in [0 .. 2*N-2]
    return @intCast(r + c);
}

inline fn right_to_left_diagonal_start(n: usize) Move {
    const i: i32 = @intCast(n);
    const start_r: i32 = if (i < N) 0 else i - (N - 1);
    const start_c: i32 = if (i < N) i else N - 1;
    return Move.at(start_r, start_c);
}

inline fn right_to_left_diagonal_length(i: usize) usize {
    const index: i32 = @as(i32, @intCast(i)); // r+c
    return @intCast(if (index < N) (index + 1) else ((2 * N - 1) - index));
}

const DIRECTIONS = [_]struct { r: i32, c: i32 }{
    .{ .r = 1, .c = 0 },
    .{ .r = 0, .c = 1 },
    .{ .r = 1, .c = 1 },
    .{ .r = 1, .c = -1 },
};

pub const Move = struct {
    r: i32,
    c: i32,

    pub inline fn at(r: i32, c: i32) Move {
        return .{ .r = r, .c = c };
    }

    pub inline fn in(self: Move) bool {
        return self.r >= 0 and self.r < N and self.c >= 0 and self.c < N;
    }

    pub inline fn invalid(self: Move) bool {
        return !self.in();
    }
};

pub const Stats = struct {
    analyzed_moves: usize = 0,
    choose_move_time_ns: u64 = 0,

    quiescence_count: usize = 0,
    quiescence_time_ns: u64 = 0,
    quiescence_time_avg_ns: u64 = 0,

    available_moves_calls: usize = 0,
    available_moves_time_ns: u64 = 0,
    available_moves_time_avg_ns: u64 = 0,

    check_pattern_calls: usize = 0,
    check_pattern_time_ns: u64 = 0,
    check_pattern_time_avg_ns: u64 = 0,

    check_patterns_calls: usize = 0,
    check_patterns_time_ns: u64 = 0,
    check_patterns_time_avg_ns: u64 = 0,

    pruning_count: usize = 0,

    pub fn reset(self: *Stats) void {
        self.analyzed_moves = 0;
        self.choose_move_time_ns = 0;

        self.quiescence_count = 0;
        self.quiescence_time_ns = 0;
        self.quiescence_time_avg_ns = 0;

        self.available_moves_calls = 0;
        self.available_moves_time_ns = 0;
        self.available_moves_time_avg_ns = 0;

        self.check_pattern_calls = 0;
        self.check_pattern_time_ns = 0;
        self.check_pattern_time_avg_ns = 0;

        self.check_patterns_calls = 0;
        self.check_patterns_time_ns = 0;
        self.check_patterns_time_avg_ns = 0;

        self.pruning_count = 0;
    }

    pub fn print(self: *const Stats) void {
        output("stats:\n", .{});
        if (!WASM) {
            output("- analyzed_moves: {any} in {any}s\n", .{ self.analyzed_moves, ns_to_s(self.choose_move_time_ns) });
            output("- quiescence_count: {any} time(s): {any}, avg(s): {any}\n", .{ self.quiescence_count, ns_to_s(self.quiescence_time_ns), ns_to_s(self.quiescence_time_avg_ns) });
            output("- available_moves calls: {any}, time(s): {any}, avg(s): {any}\n", .{ self.available_moves_calls, ns_to_s(self.available_moves_time_ns), ns_to_s(self.available_moves_time_avg_ns) });
            output("- check_pattern calls: {any}, time(s): {any}, avg(s): {any}\n", .{ self.check_pattern_calls, ns_to_s(self.check_pattern_time_ns), ns_to_s(self.check_pattern_time_avg_ns) });
            output("- a/b pruning count: {any}\n", .{self.pruning_count});
        } else {
            output("- analyzed_moves: {any}\n", .{self.analyzed_moves});
            output("- quiescence_count: {any}\n", .{self.quiescence_count});
            output("- available_moves calls: {any}\n", .{self.available_moves_calls});
            output("- check_pattern calls: {any}\n", .{self.check_pattern_calls});
            output("- a/b pruning count: {any}\n", .{self.pruning_count});
        }
    }
};

inline fn ns_to_s(ns: u64) f64 {
    return @as(f64, @floatFromInt(ns)) / std.time.ns_per_s;
}

const DIAGONALS: usize = @intCast(2 * @as(i32, N) - 1);

pub const Game = struct {
    board: [N][N]Field = [_][N]Field{[_]Field{.empty} ** N} ** N,

    // running evaluation = totals[computer] - totals[human]
    evaluation: i32 = 0,

    counters: Stats = Stats{},

    // running sum of all line scores per player:
    // totals[0] = human, totals[1] = computer
    totals: [2]i32 = .{ 0, 0 },

    // caches: score of a single line for each player, -1 = unknown
    row_cache: [N][2]i32 = [_][2]i32{[_]i32{-1} ** 2} ** N,
    col_cache: [N][2]i32 = [_][2]i32{[_]i32{-1} ** 2} ** N,

    // diagonals (↘ and ↙) have 2*N - 1 lines each
    diagonal_left_cache: [DIAGONALS][2]i32 = [_][2]i32{[_]i32{-1} ** 2} ** DIAGONALS, // ↘ (r - c constant)
    diagonal_right_cache: [DIAGONALS][2]i32 = [_][2]i32{[_]i32{-1} ** 2} ** DIAGONALS, // ↙ (r + c constant)

    // frontier for move generation
    move_stack: [NN]Move = undefined,
    stack_len: usize = 0,

    // per-position mark to avoid duplicates when building candidate list
    // uses an epoch counter so it does not have to clear the array every time
    marks: [N][N]u32 = [_][N]u32{[_]u32{0} ** N} ** N,
    mark_epoch: u32 = 1,

    inline fn mark_once(self: *Game, m: Move) bool {
        const r: usize = @intCast(m.r);
        const c: usize = @intCast(m.c);
        if (self.marks[r][c] == self.mark_epoch) return false; // already added
        self.marks[r][c] = self.mark_epoch;
        return true;
    }

    inline fn next_epoch(self: *Game) void {
        self.mark_epoch +%= 1; // wrapping add
        if (self.mark_epoch == 0) {
            // extremely unlikely, but keep it robust
            inline for (0..N) |r| {
                inline for (0..N) |c| self.marks[r][c] = 0;
            }
            self.mark_epoch = 1;
        }
    }

    pub inline fn at(self: *const Game, move: Move) Field {
        const r: usize = @intCast(move.r);
        const c: usize = @intCast(move.c);
        return self.board[r][c];
    }

    pub inline fn empty_at(self: *const Game, move: Move) bool {
        return self.at(move) == .empty;
    }

    pub inline fn place_at(self: *Game, r: i32, c: i32, player: Field) void {
        self.place(Move.at(r, c), player);
    }

    pub inline fn place(self: *Game, move: Move, player: Field) void {
        if (move.invalid()) @panic("place: invalid position");
        if (player == .empty) @panic("place: cannot place empty");
        if (self.at(move) != .empty) @panic("place: position already occupied");

        self.counters.analyzed_moves += 1;

        const r: usize = @intCast(move.r);
        const c: usize = @intCast(move.c);
        self.board[r][c] = player;

        self.move_stack[self.stack_len] = move;
        self.stack_len += 1;

        self.recompute_lines_at(move);
    }

    pub inline fn unplace_at(self: *Game, r: i32, c: i32) void {
        self.unplace(Move.at(r, c));
    }

    pub inline fn unplace(self: *Game, move: Move) void {
        if (move.invalid()) @panic("unplace: invalid position");
        if (self.at(move) == .empty) @panic("unplace: position already empty");

        const r: usize = @intCast(move.r);
        const c: usize = @intCast(move.c);
        self.board[r][c] = .empty;

        self.stack_len -= 1;
        std.debug.assert(self.move_stack[self.stack_len].r == move.r and self.move_stack[self.stack_len].c == move.c);

        self.recompute_lines_at(move);
    }

    pub fn is_full(self: *const Game) bool {
        var r: i32 = 0;
        while (r < N) : (r += 1) {
            var c: i32 = 0;
            while (c < N) : (c += 1) {
                if (self.empty_at(Move.at(r, c))) return false;
            }
        }
        return true;
    }

    pub fn check_win_at(self: *const Game, move: Move) Field {
        const player = self.at(move);
        inline for (DIRECTIONS) |dir| {
            var count: i32 = 1;
            // forward
            var v = Move.at(move.r + dir.r, move.c + dir.c);
            while (v.in() and self.at(v) == player) : (v = Move.at(v.r + dir.r, v.c + dir.c)) {
                count += 1;
            }
            // backward
            v = Move.at(move.r - dir.r, move.c - dir.c);
            while (v.in() and self.at(v) == player) : (v = Move.at(v.r - dir.r, v.c - dir.c)) {
                count += 1;
            }
            if (count >= 5) return player;
        }
        return .empty;
    }

    pub fn check_pattern(self: *Game, from: Move, dir: Move, player: Field) i32 {
        self.counters.check_pattern_calls += 1;

        var start_time: TimerType = undefined;
        if (!WASM) {
            start_time = TimerType.start() catch @panic("check_pattern: timer start failed");
        }
        defer {
            if (!WASM) {
                const elapsed = start_time.read();
                self.counters.check_pattern_time_ns += elapsed;
                self.counters.check_pattern_time_avg_ns = (self.counters.check_pattern_time_avg_ns + elapsed) / 2;
            }
        }

        var v = from;
        var buf: [N]u8 = undefined;
        var i: usize = 0;
        while (v.in()) : (v = Move.at(v.r + dir.r, v.c + dir.c)) {
            const field = self.at(v);
            if (field == player) {
                buf[i] = 'G';
            } else if (field == .empty) {
                buf[i] = '_';
            } else {
                buf[i] = '.';
            }
            i += 1;
        }
        const line = buf[0..i];

        var score: i32 = 0;
        inline for (patterns) |pattern| {
            var j: usize = 0;
            const L = pattern.value.len;
            while (j + L <= line.len) : (j += 1) {
                const match = std.mem.eql(u8, line[j .. j + L], pattern.value);
                if (match) {
                    score += pattern.weight;
                    if (score >= 10_000) return score;
                }
            }
        }
        return score;
    }

    inline fn update_player_total(self: *Game, prev: i32, new: i32, player: Field) void {
        const i = player_index(player);
        self.totals[i] += (new - prev);
    }

    fn recompute_row(self: *Game, r: i32) void {
        const start = Move.at(r, 0);
        const dir = Move.at(0, 1);
        inline for (.{ .human, .computer }) |player| {
            const i = player_index(player);
            const prev = if (self.row_cache[@intCast(r)][i] != -1)
                self.row_cache[@intCast(r)][i]
            else
                self.check_pattern(start, dir, player);
            const new = self.check_pattern(start, dir, player);
            self.row_cache[@intCast(r)][i] = new;
            self.update_player_total(prev, new, player);
        }
    }

    fn recompute_column(self: *Game, c: i32) void {
        const start = Move.at(0, c);
        const dir = Move.at(1, 0);
        inline for (.{ .human, .computer }) |player| {
            const i = player_index(player);
            const prev = if (self.col_cache[@intCast(c)][i] != -1)
                self.col_cache[@intCast(c)][i]
            else
                self.check_pattern(start, dir, player);
            const new = self.check_pattern(start, dir, player);
            self.col_cache[@intCast(c)][i] = new;
            self.update_player_total(prev, new, player);
        }
    }

    fn recompute_left_to_right_diagonal(self: *Game, diagonal: usize) void {
        if (left_to_right_diagonal_length(diagonal) < MIN_EVAL_PATTERN_LEN) {
            inline for (.{ .human, .computer }) |player| {
                const i = player_index(player);
                const prev = if (self.diagonal_left_cache[diagonal][i] != -1) self.diagonal_left_cache[diagonal][i] else 0;
                const new = 0;
                self.diagonal_left_cache[diagonal][i] = new;
                self.update_player_total(prev, new, player);
            }
            return;
        }

        const start = left_to_right_diagonal_start(diagonal);
        const dir = Move.at(1, 1);
        inline for (.{ .human, .computer }) |player| {
            const i = player_index(player);
            const prev = if (self.diagonal_left_cache[diagonal][i] != -1)
                self.diagonal_left_cache[diagonal][i]
            else
                self.check_pattern(start, dir, player);
            const new = self.check_pattern(start, dir, player);
            self.diagonal_left_cache[diagonal][i] = new;
            self.update_player_total(prev, new, player);
        }
    }

    fn recompute_right_to_left_diagonal(self: *Game, diagonal: usize) void {
        if (right_to_left_diagonal_length(diagonal) < MIN_EVAL_PATTERN_LEN) {
            inline for (.{ .human, .computer }) |player| {
                const i = player_index(player);
                const prev = if (self.diagonal_right_cache[diagonal][i] != -1) self.diagonal_right_cache[diagonal][i] else 0;
                const new = 0;
                self.diagonal_right_cache[diagonal][i] = new;
                self.update_player_total(prev, new, player);
            }
            return;
        }

        const start = right_to_left_diagonal_start(diagonal);
        const dir = Move.at(1, -1);
        inline for (.{ .human, .computer }) |player| {
            const i = player_index(player);
            const prev = if (self.diagonal_right_cache[diagonal][i] != -1)
                self.diagonal_right_cache[diagonal][i]
            else
                self.check_pattern(start, dir, player);
            const new = self.check_pattern(start, dir, player);
            self.diagonal_right_cache[diagonal][i] = new;
            self.update_player_total(prev, new, player);
        }
    }

    fn recompute_lines_at(self: *Game, rc: Move) void {
        self.recompute_row(rc.r);
        self.recompute_column(rc.c);
        self.recompute_left_to_right_diagonal(left_to_right_diagonal_index(rc.r, rc.c));
        self.recompute_right_to_left_diagonal(right_to_left_diagonal_index(rc.r, rc.c));

        self.evaluation = self.totals[player_index(.computer)] - self.totals[player_index(.human)];
    }

    // batch scanner: useful for validation or profiling
    pub fn check_patterns(self: *Game, player: Field) i32 {
        self.counters.check_patterns_calls += 1;

        var start_time: TimerType = undefined;
        if (!WASM) {
            start_time = TimerType.start() catch @panic("check_patterns: timer start failed");
        }
        defer {
            if (!WASM) {
                const elapsed = start_time.read();
                self.counters.check_patterns_time_ns += elapsed;
                self.counters.check_patterns_time_avg_ns = (self.counters.check_patterns_time_avg_ns + elapsed) / 2;
            }
        }

        var score: i32 = 0;

        // rows
        inline for (0..N) |r|
            score += self.check_pattern(Move.at(@intCast(r), 0), Move.at(0, 1), player);

        // columns
        inline for (0..N) |c|
            score += self.check_pattern(Move.at(0, @intCast(c)), Move.at(1, 0), player);

        // diagonal ↘
        inline for (0..@intCast(DIAGONALS)) |k| {
            if (left_to_right_diagonal_length(k) >= MIN_EVAL_PATTERN_LEN) {
                score += self.check_pattern(left_to_right_diagonal_start(k), Move.at(1, 1), player);
            }
        }

        // diagonal ↙
        inline for (0..@intCast(DIAGONALS)) |k| {
            if (right_to_left_diagonal_length(k) >= MIN_EVAL_PATTERN_LEN) {
                score += self.check_pattern(right_to_left_diagonal_start(k), Move.at(1, -1), player);
            }
        }
        return score;
    }

    pub inline fn evaluate_static(self: *Game) i32 {
        return self.evaluation;
    }

    pub fn available_moves(self: *Game, backing: *[NN]Move) []Move {
        self.counters.available_moves_calls += 1;

        var start_time: TimerType = undefined;
        if (!WASM) {
            start_time = TimerType.start() catch @panic("available_moves: timer start failed");
        }
        defer {
            if (!WASM) {
                const elapsed = start_time.read();
                self.counters.available_moves_time_ns += elapsed;
                self.counters.available_moves_time_avg_ns = (self.counters.available_moves_time_avg_ns + elapsed) / 2;
            }
        }

        // play center if first move
        if (self.stack_len == 0) {
            backing[0] = Move.at(@intCast(N / 2), @intCast(N / 2));
            return backing[0..1];
        }

        // build candidates by scanning the neighborhood around each played move
        // radius 1 (8-neighborhood) is typical; bump to 2 if you want a bit more breadth
        const R: i32 = 1;

        self.next_epoch(); // start fresh dedup epoch
        var n: usize = 0;

        var i: usize = 0;
        while (i < self.stack_len) : (i += 1) {
            const origin = self.move_stack[i];

            var dr: i32 = -R;
            while (dr <= R) : (dr += 1) {
                var dc: i32 = -R;
                while (dc <= R) : (dc += 1) {
                    if (dr == 0 and dc == 0) continue;
                    const v = Move.at(origin.r + dr, origin.c + dc);
                    if (!v.in()) continue;
                    if (!self.empty_at(v)) continue;

                    // dedup across all origins
                    if (!self.mark_once(v)) continue;

                    backing[n] = v;
                    n += 1;
                }
            }
        }

        comptime {
            @setEvalBranchQuota(100_000);
        }

        // fallback: if somehow no candidates (almost-full board edge case), scan once.
        if (n == 0) {
            inline for (0..N) |r| {
                inline for (0..N) |c| {
                    const m = Move.at(@intCast(r), @intCast(c));
                    if (self.empty_at(m)) {
                        backing[n] = m;
                        n += 1;
                    }
                }
            }
        }

        return backing[0..n];
    }

    const TimerType = if (WASM) void else std.time.Timer;

    pub fn choose_move(self: *Game, depth: i32, player: Field) Move {
        self.counters.reset();

        var start_time: TimerType = undefined;
        if (!WASM) {
            start_time = TimerType.start() catch @panic("choose_move: timer start failed");
        }
        defer {
            if (!WASM) {
                const elapsed = start_time.read();
                self.counters.choose_move_time_ns = elapsed;
            }
        }

        var backing: [NN]Move = undefined;
        const moves = self.available_moves(&backing);
        if (moves.len == 0) @panic("choose_move: no available moves");
        if (moves.len == 1) return moves[0];

        self.order_moves(moves, player); // pre-order for first move optimization

        var best_move: ?Move = null;
        var best_value: i32 = if (player == .computer) -std.math.maxInt(i32) else std.math.maxInt(i32);

        for (moves, 1..) |move, i| {
            progress(i, moves.len, &self.counters);

            self.place(move, player);

            const opponent: Field = if (player == .computer) .human else .computer;
            const value = self.minimax(depth - 1, opponent, -std.math.maxInt(i32), std.math.maxInt(i32), move);

            self.unplace(move);

            if (player == .computer) {
                if (value > best_value) {
                    best_value = value;
                    best_move = move;
                }
            } else {
                if (value < best_value) {
                    best_value = value;
                    best_move = move;
                }
            }
        }

        if (best_move == null) @panic("choose_move: no best move found");
        return best_move.?;
    }

    fn minimax(self: *Game, depth: i32, player: Field, alpha_: i32, beta_: i32, entry_move: Move) i32 {
        const winner = self.check_win_at(entry_move);
        if (winner != .empty) {
            return if (winner == .computer) 1_000_000 else -1_000_000;
        }

        var backing: [NN]Move = undefined;
        const moves = self.available_moves(&backing);

        if (depth == 0 or moves.len == 0) {
            // quiescence instead of a hard horizon cut
            if (QDEPTH > 0)
                return self.quiescence(QDEPTH, player, alpha_, beta_);
            return self.evaluate_static();
        }

        // order moves by immediate win or by delta to improve pruning
        if (ORDER_MOVES) self.order_moves(moves, player);

        var alpha = alpha_;
        var beta = beta_;

        for (moves) |move| {
            self.place(move, player);
            const opponent: Field = if (player == .computer) .human else .computer;
            const score = self.minimax(depth - 1, opponent, alpha, beta, move);
            self.unplace(move);

            if (player == .computer) {
                if (score > alpha) alpha = score;
            } else {
                if (score < beta) beta = score;
            }

            if (beta <= alpha) {
                self.counters.pruning_count += 1;
                break; // cutoff
            }
        }
        return if (player == .computer) alpha else beta;
    }

    /// Larger is better for .computer, smaller for .human
    fn move_delta(self: *Game, mv: Move, player: Field) i32 {
        const before = self.evaluate_static();
        self.place(mv, player);
        const after = self.evaluate_static();
        self.unplace(mv);
        return after - before;
    }

    /// Returns true if this move is "tactical": wins now, blocks an immediate win,
    /// or swings eval by a large amount (forcing moves / big threats).
    fn is_tactical(self: *Game, move: Move, player: Field) bool {
        // 1. our immediate win?
        self.place(move, player);
        var winner = self.check_win_at(move);
        self.unplace(move);
        if (winner == player) return true;

        // 2. blocks opponent's immediate win?
        const opponents: Field = if (player == .computer) .human else .computer;
        self.place(move, opponents);
        winner = self.check_win_at(move);
        self.unplace(move);
        if (winner == opponents) return true; // if opponent could win by playing here, blocking is tactical

        // 3. big heuristic swing?
        const delta = self.move_delta(move, player);
        return @abs(delta) >= QUIET_THRESHOLD;
    }

    /// Orders `moves` in-place: best-first for the side to move.
    /// We score by immediate win then evaluation delta.
    fn order_moves(self: *Game, moves: []Move, player: Field) void {
        if (moves.len <= 1) return;

        var scores: [NN]i32 = undefined;

        // pre-score
        var i: usize = 0;
        while (i < moves.len) : (i += 1) {
            const move = moves[i];

            // immediate win?
            self.place(move, player);
            const winner = self.check_win_at(move);
            self.unplace(move);
            var score: i32 = if (winner == player) 2_000_000 else self.move_delta(move, player);

            // for the minimizing side, invert to still sort descending
            if (player == .human) score = -score;

            scores[i] = score;
        }

        // insertion sort (small arrays)
        var k: usize = 1;
        while (k < moves.len) : (k += 1) {
            const key_move = moves[k];
            const key_score = scores[k];
            var j = k;
            while (j > 0 and scores[j - 1] < key_score) : (j -= 1) {
                scores[j] = scores[j - 1];
                moves[j] = moves[j - 1];
            }
            scores[j] = key_score;
            moves[j] = key_move;
        }
    }

    fn quiescence(self: *Game, qdepth: i32, player: Field, alpha_: i32, beta_: i32) i32 {
        var alpha = alpha_;
        var beta = beta_;
        const stand_pat = self.evaluate_static();

        if (player == .computer) {
            if (stand_pat >= beta) return beta;
            if (stand_pat > alpha) alpha = stand_pat;
        } else {
            if (stand_pat <= alpha) return alpha;
            if (stand_pat < beta) beta = stand_pat;
        }

        if (qdepth <= 0) return stand_pat;

        self.counters.quiescence_count += 1;

        var start_time: TimerType = undefined;
        if (!WASM) {
            start_time = TimerType.start() catch @panic("quiescence: timer start failed");
        }
        defer {
            if (!WASM) {
                const elapsed = start_time.read();
                self.counters.quiescence_time_ns += elapsed;
                self.counters.quiescence_time_avg_ns = (self.counters.quiescence_time_avg_ns + elapsed) / 2;
            }
        }

        var backing: [NN]Move = undefined;
        var noisy_backing: [NN]Move = undefined;

        const moves = self.available_moves(&backing);

        var n: usize = 0;
        for (moves) |move| {
            if (self.is_tactical(move, player)) {
                noisy_backing[n] = move;
                n += 1;
            }
        }
        const noisy = noisy_backing[0..n];

        if (noisy.len == 0) return stand_pat;

        self.order_moves(noisy, player);

        for (noisy) |move| {
            self.place(move, player);

            // explicit terminal check to cut immediately on wins
            const winner = self.check_win_at(move);
            if (winner != .empty) {
                const score: i32 = if (winner == .computer) 1_000_000 else -1_000_000;
                self.unplace(move);

                if (player == .computer) {
                    if (score > alpha) alpha = score;
                } else {
                    if (score < beta) beta = score;
                }

                if (beta <= alpha) {
                    self.counters.pruning_count += 1;
                    break;
                }
                // continue to next noisy move if no cutoff
                continue;
            }

            const opponents: Field = if (player == .computer) .human else .computer;
            const score = self.quiescence(qdepth - 1, opponents, alpha, beta);
            self.unplace(move);

            if (player == .computer) {
                if (score > alpha) alpha = score;
            } else {
                if (score < beta) beta = score;
            }

            if (beta <= alpha) break;
        }

        return if (player == .computer) alpha else beta;
    }

    pub fn print_board(self: *const Game) void {
        output("\n", .{});
        for (self.board, 0..) |row, r| {
            output("{d: <2} | ", .{r});
            for (row) |field| {
                const c: u8 = switch (field) {
                    .empty => '.',
                    .human => 'X',
                    .computer => 'O',
                };
                output("{c} ", .{c});
            }
            output("\n", .{});
        }
    }

    const ANSI_RESET = "\x1b[0m";

    const ANSI_GREEN = "\x1b[32m";
    const ANSI_YELLOW = "\x1b[33m";
    const ANSI_MAGENTA = "\x1b[35m";
    const ANSI_CYAN = "\x1b[36m";

    const ANSI_BOLD = "\x1b[1m";

    pub fn print_board_at(self: *const Game, move: Move) void {
        output("\n", .{});
        for (self.board, 0..) |row, r| {
            output("{d: <2} | ", .{r});
            const first: u8 = if (r == move.r and move.c == 0) '[' else ' ';
            output("{c}", .{first});
            for (row, 0..) |field, c| {
                const v: struct { color: []const u8, player: u8 } = switch (field) {
                    .empty => .{ .color = ANSI_GREEN, .player = '.' },
                    .human => .{ .color = ANSI_MAGENTA, .player = 'X' },
                    .computer => .{ .color = ANSI_CYAN, .player = 'O' },
                };
                const f = Move.at(@intCast(r), @intCast(c));
                const is_move = (move.r == f.r and move.c == f.c);
                const bold = if (is_move) ANSI_BOLD else "";

                const bracket: u8 = if (r == move.r and c == move.c) ']' else (if (r == move.r and c == move.c - 1) '[' else ' ');
                output("{s}{s}{c}{s}{c}", .{ v.color, bold, v.player, ANSI_RESET, bracket });
            }
            output("\n", .{});
        }
    }

    pub fn init() Game {
        var game = Game{};
        for (0..N) |r| {
            for (0..N) |c| {
                game.board[@intCast(r)][@intCast(c)] = .empty;
            }
        }
        return game;
    }
};

pub fn main() void {
    loopback();
}

pub export fn loopback() void {
    var game = Game.init();

    const first_move = Move.at(7, 7);
    game.place(first_move, .human);
    game.print_board_at(first_move);

    var player: Field = .computer;
    while (true) {
        output("thinking...\n", .{});
        const move = game.choose_move(DEPTH, player);
        game.place(move, player);
        game.print_board_at(move);
        output("{any}: {any}\n", .{ player, move });

        const winner = game.check_win_at(move);
        if (winner != .empty) {
            output("winner: {any}\n", .{winner});
            break;
        }
        player = if (player == .computer) .human else .computer;

        game.counters.print();

        wait_enter() catch {};
    }
}

pub const patterns: [16]Pattern = [_]Pattern{
    Pattern{ .value = "GGGGG", .weight = 10000 },
    Pattern{ .value = "_GGGG_", .weight = 500 },
    Pattern{ .value = "GGG_G", .weight = 100 },
    Pattern{ .value = "GG_GG", .weight = 100 },
    Pattern{ .value = "G_GGG", .weight = 100 },
    Pattern{ .value = "_GGGG", .weight = 100 },
    Pattern{ .value = "GGGG_", .weight = 100 },
    Pattern{ .value = "_GG_G_", .weight = 10 },
    Pattern{ .value = "_G_GG_", .weight = 10 },
    Pattern{ .value = "_GGG_", .weight = 10 },
    Pattern{ .value = "GGG_", .weight = 10 },
    Pattern{ .value = "_GGG", .weight = 10 },
    Pattern{ .value = "_G_G_", .weight = 2 },
    Pattern{ .value = "_GG_", .weight = 2 },
    Pattern{ .value = "_GG", .weight = 1 },
    Pattern{ .value = "GG_", .weight = 1 },
};

const Pattern = struct {
    value: []const u8,
    weight: i32,
};

pub fn wait_enter() !void {
    if (WASM) {
        enter();
        return;
    }

    output("press enter to continue...\n", .{});

    var in_buf: [64]u8 = undefined;
    var in_reader = std.fs.File.stdin().readerStreaming(&in_buf);
    const input = &in_reader.interface;
    while (true) {
        const b = input.takeByte() catch |err| switch (err) {
            error.EndOfStream => break,
            else => return err,
        };
        if (b == '\n') break;
    }
}

pub fn output(comptime fmt: []const u8, args: anytype) void {
    if (WASM) {
        var buffer: [1024]u8 = undefined;
        const v = std.fmt.bufPrint(&buffer, fmt, args) catch return;
        console(v.ptr, v.len);
    } else {
        std.debug.print(fmt, args);
    }
}

pub fn progress(i: usize, n: usize, stats: *const Stats) void {
    if (builtin.is_test) {
        return;
    }
    const crlf = if (i == n) "\n" else "\r";
    const percent: f64 = @as(f64, @floatFromInt(i)) / @as(f64, @floatFromInt(n)) * 100.0;

    var buffer: [1024]u8 = undefined;
    const fmt = "{any: <.2}% ({any}/{any}) ({d}) {s}";
    const args = .{ percent, i, n, stats.analyzed_moves, crlf };

    const v = std.fmt.bufPrint(&buffer, fmt, args) catch return;
    output("{s}", .{v});

    if (WASM) {
        status(v.ptr, v.len);
    }
}
