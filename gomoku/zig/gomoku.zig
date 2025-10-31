const std = @import("std");
const eql = std.mem.eql;
const testing = std.testing;

const DEPTH = 4;
const QDEPTH: i32 = 1; // tune 2..6 based on speed
const ORDER_MOVES = false; // tune true/false based on speed

pub const N: i8 = 15;
pub const NN: usize = @as(i16, N) * N;

const Field = enum {
    empty,
    human,
    computer,
};

const DIRECTIONS = [_]struct { r: i32, c: i32 }{
    .{ .r = 1, .c = 0 },
    .{ .r = 0, .c = 1 },
    .{ .r = 1, .c = 1 },
    .{ .r = 1, .c = -1 },
};

pub const Move = struct {
    r: i32,
    c: i32,

    pub fn at(r: i32, c: i32) Move {
        return .{ .r = r, .c = c };
    }

    pub fn is_empty(self: Move) bool {
        return self.r == -1 and self.c == -1;
    }

    pub fn in(self: Move) bool {
        return self.r >= 0 and self.r < N and self.c >= 0 and self.c < N;
    }

    pub fn invalid(self: Move) bool {
        return !self.in();
    }

    pub fn format(
        self: *const Move,
        comptime fmt: []const u8,
        options: std.fmt.FormatOptions,
        writer: anytype,
    ) !void {
        _ = fmt; // unused
        _ = options; // unused
        try writer.print("Move{{ r = {}, c = {} }}", .{ self.r, self.c });
    }
};

pub const Game = struct {
    board: [N][N]Field = [_][N]Field{[_]Field{.empty} ** N} ** N,

    pub inline fn at(self: *const Game, m: Move) Field {
        const r: usize = @intCast(m.r);
        const c: usize = @intCast(m.c);
        return self.board[r][c];
    }

    pub inline fn empty_at(self: *const Game, m: Move) bool {
        return self.at(m) == .empty;
    }

    pub inline fn place(self: *Game, m: Move, player: Field) void {
        if (m.invalid()) unreachable;
        if (self.at(m) != .empty) unreachable;
        const r: usize = @intCast(m.r);
        const c: usize = @intCast(m.c);
        self.board[r][c] = player;
    }

    pub inline fn unplace(self: *Game, m: Move) void {
        const r: usize = @intCast(m.r);
        const c: usize = @intCast(m.c);
        self.board[r][c] = .empty;
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

    pub fn check_win(self: *const Game) Field {
        var r: i32 = 0;
        while (r < N) : (r += 1) {
            var c: i32 = 0;
            while (c < N) : (c += 1) {
                const m = Move.at(r, c);
                if (self.empty_at(m)) continue;
                const field = self.at(m);
                if (self.check_win_at(m) != .empty) return field;
            }
        }
        return .empty;
    }

    fn check_win_at(self: *const Game, move: Move) Field {
        const player = self.at(move);
        for (DIRECTIONS) |dir| {
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

    pub fn check_pattern(self: *const Game, from: Move, dir: Move, player: Field) i32 {
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
        for (patterns) |pattern| {
            var j: usize = 0;
            while (j + pattern.len <= line.len) : (j += 1) {
                const part = line[j .. j + pattern.len];
                const match = std.mem.eql(u8, part, pattern.pattern);
                if (match) {
                    score += pattern.weight;
                    if (score >= 10_000) return score;
                }
            }
        }
        return score;
    }

    pub fn check_patterns(self: *const Game, player: Field) i32 {
        var score: i32 = 0;

        // rows
        for (0..N) |r| {
            score += self.check_pattern(Move.at(@intCast(r), 0), Move.at(0, 1), player);
        }

        // columns
        for (0..N) |c| {
            score += self.check_pattern(Move.at(0, @intCast(c)), Move.at(1, 0), player);
        }

        // diagonal left top to right bottom, left edge
        for (0..N - 4) |k| {
            score += self.check_pattern(Move.at(@intCast(k), 0), Move.at(1, 1), player);
        }

        // diagonal left top to right bottom, top edge
        for (1..N - 4) |k| {
            score += self.check_pattern(Move.at(0, @intCast(k)), Move.at(1, 1), player);
        }

        // diagonal right top to left bottom, right edge
        for (0..N - 4) |k| {
            score += self.check_pattern(Move.at(@intCast(k), @intCast(N - 1)), Move.at(1, -1), player);
        }

        // diagonal right top to left bottom, top edge
        for (1..N - 4) |k| {
            score += self.check_pattern(Move.at(0, @intCast(N - 1 - k)), Move.at(1, -1), player);
        }

        return score;
    }

    pub fn evaluate_static(self: *const Game) i32 {
        return self.check_patterns(.computer) - self.check_patterns(.human);
    }

    pub fn available_moves(self: *const Game, backing: *[NN]Move) []Move {
        var empties: usize = 0;
        var n: usize = 0;
        for (0..N) |r| {
            for (0..N) |c| {
                const m = Move.at(@intCast(r), @intCast(c));
                if (self.empty_at(m)) {
                    empties += 1;
                    if (self.have_adjacent_fields(m)) {
                        backing[n] = m;
                        n += 1;
                    }
                }
            }
        }
        if (empties == NN) {
            backing[0] = Move.at(@intCast(N / 2), @intCast(N / 2));
            return backing[0..1];
        }
        return backing[0..n];
    }

    fn have_adjacent_fields(self: *const Game, m: Move) bool {
        const M = 1;
        var r: i32 = -M;
        while (r <= M) : (r += 1) {
            var c: i32 = -M;
            while (c <= M) : (c += 1) {
                if (r == 0 and c == 0) continue;
                const v = Move.at(m.r + r, m.c + c);
                if (v.in() and !self.empty_at(v)) {
                    return true;
                }
            }
        }
        return false;
    }

    pub fn choose_move(self: *Game, depth: i32, player: Field) Move {
        var backing: [NN]Move = undefined;
        const moves = self.available_moves(&backing);
        if (moves.len == 0) @panic("choose_move: no available moves");

        if (moves.len == 1) return moves[0];

        // order root moves for better pruning
        self.order_moves(moves, player);

        var best_move: ?Move = null;
        var best_value: i32 = if (player == .computer)
            -std.math.maxInt(i32)
        else
            std.math.maxInt(i32);

        for (moves) |move| {
            self.place(move, player);

            // If this move wins immediately, no need to search deeper.
            const winner = self.check_win_at(move);
            const value: i32 = if (winner != .empty)
                (if (winner == .computer) 1_000_000 else -1_000_000)
            else blk: {
                const opponent: Field = if (player == .computer) .human else .computer;
                break :blk self.minimax(depth - 1, opponent, -std.math.maxInt(i32), std.math.maxInt(i32));
            };

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

    fn minimax(self: *Game, depth: i32, player: Field, alpha_: i32, beta_: i32) i32 {
        const winner = self.check_win();
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
            const score = self.minimax(depth - 1, opponent, alpha, beta);
            self.unplace(move);

            if (player == .computer) {
                if (score > alpha) alpha = score;
            } else {
                if (score < beta) beta = score;
            }

            if (beta <= alpha) break; // cutoff
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
        // 1) our immediate win?
        self.place(move, player);
        var winner = self.check_win_at(move);
        self.unplace(move);
        if (winner == player) return true;

        // 2) blocks opponent's immediate win?
        const opponents: Field = if (player == .computer) .human else .computer;
        self.place(move, opponents);
        winner = self.check_win_at(move);
        self.unplace(move);
        if (winner == opponents) return true; // if opponent could win by playing here, blocking is tactical

        // 3) big heuristic swing?
        const QUIET_THRESHOLD: i32 = 90; // ~ bigger than any 10/2/1 patterns, close to 100s
        const delta = self.move_delta(move, player);
        return @abs(delta) >= QUIET_THRESHOLD;
    }

    /// Orders `moves` in-place: best-first for the side to move.
    /// We score by immediate win is much greater than evaluation delta,
    /// for minimizing side we invert scores.
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

        // simple insertion sort (small arrays, works well + minimal dependencies)
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
        // stand-pat evaluation (always computer's perspective)
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

        // consider only "tactical/noisy" moves
        var backing: [NN]Move = undefined;
        var noisy_backing: [NN]Move = undefined;

        const moves = self.available_moves(&backing);

        // filter to tactical
        var n: usize = 0;
        for (moves) |move| {
            if (self.is_tactical(move, player)) {
                noisy_backing[n] = move;
                n += 1;
            }
        }
        const noisy = noisy_backing[0..n];

        if (noisy.len == 0) return stand_pat;

        // order tactical moves best-first
        self.order_moves(noisy, player);

        for (noisy) |move| {
            self.place(move, player);
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
        std.debug.print("\n", .{});
        for (self.board) |row| {
            for (row) |field| {
                const c: u8 = switch (field) {
                    .empty => '.',
                    .human => 'X',
                    .computer => 'O',
                };
                std.debug.print("{c} ", .{c});
            }
            std.debug.print("\n", .{});
        }
    }

    const ANSI_RESET = "\x1b[0m";
    const ANSI_YELLOW = "\x1b[33m";

    pub fn print_board_at(self: *const Game, move: Move) void {
        std.debug.print("\n", .{});
        for (self.board, 0..) |row, r| {
            for (row, 0..) |field, c| {
                const ch: u8 = switch (field) {
                    .empty => '.',
                    .human => 'X',
                    .computer => 'O',
                };
                const v = Move.at(@intCast(r), @intCast(c));
                const color = if (move.r == v.r and move.c == v.c) ANSI_YELLOW else "";
                std.debug.print("{s}{c}{s} ", .{ color, ch, ANSI_RESET });
            }
            std.debug.print("\n", .{});
        }
    }

    pub fn from_text(lines: []const []const u8) Game {
        var game = Game{};
        var r: i32 = 0;
        while (r < N) : (r += 1) {
            const line = lines[@intCast(r)];
            var c: i32 = 0;
            while (c < N) : (c += 1) {
                const ch = line[@intCast(c)];
                const field: Field = switch (ch) {
                    'X' => .human,
                    'O' => .computer,
                    '.' => .empty,
                    else => unreachable,
                };
                game.place(Move.at(r, c), field);
            }
        }
        return game;
    }
};

pub fn main() void {
    const board = [_][]const u8{
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
    };
    var game = Game.from_text(&board);

    const first_move = Move.at(7, 7);
    game.place(first_move, .human);
    game.print_board_at(first_move);

    var player: Field = .computer;
    while (true) {
        const move = game.choose_move(DEPTH, player);
        game.place(move, player);
        game.print_board_at(move);
        std.debug.print("move by {any}: {any}\n", .{ player, move });

        const winner = game.check_win();
        if (winner != .empty) {
            std.debug.print("winner: {any}\n", .{winner});
            break;
        }
        player = if (player == .computer) .human else .computer;

        enter() catch {};
    }
}

const PATTERNS =
    \\ GGGGG,10000
    \\ _GGGG_,500
    \\ GGG_G,100
    \\ GG_GG,100
    \\ G_GGG,100
    \\ _GGGG,100
    \\ GGGG_,100
    \\ _GG_G_,10
    \\ _G_GG_,10
    \\ _GGG_,10
    \\ GGG_,10
    \\ _GGG,10
    \\ _G_G_,2
    \\ _GG_,2
    \\ _GG,1
    \\ GG_,1
;

const Pattern = struct {
    pattern: []const u8, // slice into the multiline literal
    len: usize,
    weight: i32,
};

inline fn is_ws(c: u8) bool {
    return switch (c) {
        ' ', '\t', '\r' => true,
        else => false,
    };
}

fn trim_slice(v: []const u8) []const u8 {
    var start: usize = 0;
    var end: usize = v.len;

    while (start < end and is_ws(v[start])) start += 1;
    while (end > start and is_ws(v[end - 1])) end -= 1;

    return v[start..end];
}

fn count_non_empty_lines(comptime lines: []const u8) comptime_int {
    var count: usize = 0;
    var i: usize = 0;
    var start: usize = 0;
    while (i <= lines.len) : (i += 1) {
        if (i == lines.len or lines[i] == '\n') {
            const line = trim_slice(lines[start..i]);
            if (line.len != 0) count += 1;
            start = i + 1;
        }
    }
    return count;
}

fn build_patterns(comptime lines: []const u8) [count_non_empty_lines(lines)]Pattern {
    comptime {
        @setEvalBranchQuota(100_000);
    }
    var v: [count_non_empty_lines(lines)]Pattern = undefined;

    var n: usize = 0;

    var start: usize = 0;
    var i: usize = 0;
    while (i <= lines.len) : (i += 1) {
        if (i == lines.len or lines[i] == '\n') {
            var line = trim_slice(lines[start..i]);
            if (line.len != 0) {
                const command_index_maybe = std.mem.indexOfScalar(u8, line, ',');
                if (command_index_maybe == null) @compileError("missing comma: \"" ++ line ++ "\"");
                const comma_index = command_index_maybe.?;

                const patterns_slice = trim_slice(line[0..comma_index]);
                const weight_slice = trim_slice(line[comma_index + 1 ..]);

                const weight = std.fmt.parseInt(i32, weight_slice, 10) catch @compileError("invalid weight in line: \"" ++ line ++ "\"");

                v[n] = .{
                    .pattern = patterns_slice, // slice into the original literal (static storage)
                    .len = patterns_slice.len,
                    .weight = weight,
                };
                n += 1;
            }
            start = i + 1;
        }
    }
    return v;
}

pub const patterns: []const Pattern = &build_patterns(PATTERNS);

pub fn enter() !void {
    var out_buf: [256]u8 = undefined;
    var out_writer = std.fs.File.stdout().writer(&out_buf);
    const out = &out_writer.interface;

    var in_buf: [64]u8 = undefined;
    var in_reader = std.fs.File.stdin().readerStreaming(&in_buf);
    const input = &in_reader.interface;

    try out.print("press enter to continue...\n", .{});
    while (true) {
        const b = input.takeByte() catch |err| switch (err) {
            error.EndOfStream => break,
            else => return err,
        };
        if (b == '\n') break;
    }

    try out.flush();
}
