const std = @import("std");
const eql = std.mem.eql;
const testing = std.testing;

const gomoku = @import("gomoku.zig");
const Game = gomoku.Game;
const Move = gomoku.Move;
const N = gomoku.N;
const NN = gomoku.NN;
const patterns = gomoku.patterns;

test "choose move" {
    const board = [_][]const u8{
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        ".......X.......",
        ".......OX......",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
    };
    var game = Game.from_text(&board);

    const move = game.choose_move(3, .computer);
    try testing.expectEqual(Move{ .r = 6, .c = 6 }, move);
}

test "available moves" {
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

    var backing: [NN]Move = undefined;

    const moves = game.available_moves(&backing);
    try testing.expectEqual(1, moves.len);
    try testing.expectEqual(7, moves[0].r);
    try testing.expectEqual(7, moves[0].c);

    game.place(moves[0], .human);
    try testing.expectEqual(8, game.available_moves(&backing).len);

    game.place(Move.at(7, 8), .computer);
    try testing.expectEqual(10, game.available_moves(&backing).len);
}

test "check pattern" {
    const board = [_][]const u8{
        "...............",
        "..X............",
        "...X...........",
        "....X..........",
        ".....X.........",
        "...............",
        ".......X.......",
        ".......X.......",
        ".......X.......",
        ".......X.......",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
    };

    var game = Game.from_text(&board);
    // game.print_board();
    const score = game.check_patterns(.human);
    try testing.expectEqual(score, 1544);
}

test "check winner" {
    const board = [_][]const u8{
        "...............",
        "..X............",
        "...X...........",
        "....X..........",
        ".....X.........",
        "......X........",
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
    // game.print_board();
    const winner = game.check_win();
    try testing.expectEqual(.human, winner);
}

test "place_unplace_empty_at" {
    var game = Game{};
    try testing.expect(game.empty_at(Move.at(7, 7)));
    game.place(Move.at(7, 7), .human);
    try testing.expect(!game.empty_at(Move.at(7, 7)));
    game.unplace(Move.at(7, 7));
    try testing.expect(game.empty_at(Move.at(7, 7)));
}

test "is_full" {
    var game = Game{};
    try testing.expect(!game.is_full());

    var r: i32 = 0;
    while (r < N) : (r += 1) {
        var c: i32 = 0;
        while (c < N) : (c += 1) {
            game.place(Move.at(r, c), .human);
        }
    }

    try testing.expect(game.is_full());
}

test "build_patterns works" {
    comptime {
        try std.testing.expect(patterns.len == 16);

        try std.testing.expect(eql(u8, patterns[0].pattern, "GGGGG"));
        try std.testing.expect(patterns[0].weight == 10_000);
        try std.testing.expect(eql(u8, patterns[1].pattern, "_GGGG_"));
        try std.testing.expect(patterns[1].weight == 500);

        try std.testing.expect(eql(u8, patterns[15].pattern, "GG_"));
        try std.testing.expect(patterns[15].weight == 1);
    }
}
