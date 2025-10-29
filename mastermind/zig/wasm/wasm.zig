const std = @import("std");
const allocator = std.heap.wasm_allocator;

const mastermind = @import("mastermind.zig");

inline fn castHandle(handle: usize) ?*mastermind.Game {
    if (handle == 0) return null; // 0 = null/invalid
    return @ptrFromInt(handle);
}

pub export fn init() usize {
    // allocate space for the Game
    const game = allocator.create(mastermind.Game) catch return 0;

    // initialize the struct value into the allocated memory
    game.* = mastermind.Game.init();
    // return the handle (pointer as integer) to JS
    return @intFromPtr(game);
}

pub export fn deinit(handle: usize) void {
    const game = castHandle(handle) orelse return;
    allocator.destroy(game);
}

pub export fn remaining(handle: usize) i32 {
    const game = castHandle(handle) orelse return -1;
    return game.remaining;
}

pub export fn tries(handle: usize) i32 {
    const game = castHandle(handle) orelse return -1;
    return game.tries;
}

pub export fn guess(handle: usize, in_place: i32, by_value: i32) i32 {
    const game = castHandle(handle) orelse return -1;
    return game.guess(in_place, by_value);
}
