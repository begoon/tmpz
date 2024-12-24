const std = @import("std");

const chroma = @import("chroma");

pub fn main() !void {
    std.debug.print(chroma.format("{blue}{underline}eventually{reset}, the {red}formatting{reset} looks like {130;43;122}{s}!\n"), .{"this"});
}
