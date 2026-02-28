# zig-path

A CLI tool that displays the PATH environment variable split into individual directories with color coding and entry counts.

## Build & Test

```text
zig build          # build + install to ~/bin/paths
zig build test     # run unit tests
zig build run      # build and run
just               # runs test then build
```

Requires Zig 0.16.0-dev (uses the new `std.process.Init` main signature and `std.Io` abstraction).

## Architecture

Single file: `main.zig`. No external dependencies.

### Two modes

- **Default mode**: prints all unique PATH entries to stdout with color and file counts
- **Interactive mode** (`-i` flag): fullscreen TUI selector with scrolling, runs `ls -al <path> | less` on Enter

### Key functions

- `main()` — entry point, parses `-i` flag via `std.process.Args.Iterator.init(init.minimal.args)`
- `printEntry()` — prints a single PATH entry with colors (used in default mode)
- `renderList()` — draws the interactive list with ANSI codes (used in interactive mode)
- `interactiveMode()` — main loop: raw terminal mode, keypress handling, scrolling
- `runLs()` — spawns `sh -c "ls -al '<path>' | less"` via `std.process.spawn()`
- `countEntries()` — counts non-directory entries in a path (shows file count next to each entry)
- `findSpecialPrefix()` — matches paths starting with /opt/homebrew, /opt/workbrew, /opt/zerobrew
- `shortenHome()` — replaces $HOME prefix with `~`
- `collectPaths()` — splits PATH, deduplicates, collects into ArrayList

### Color scheme

- Yellow: paths under $HOME (entire path colored)
- Blue: special prefix portion (/opt/homebrew etc), rest in default color
- White + strikethrough: non-existent directories (with cross mark)
- Dim: file count suffix `(N)`
- Reverse + bold: selected item in interactive mode

### Interactive mode details

- Terminal raw mode via `std.posix.tcgetattr`/`tcsetattr`
- Terminal height via `std.c.ioctl` with `TIOCGWINSZ`
- Direct stdout writes via `std.c.write` (bypasses buffering)
- Direct stdin reads via `std.c.read`
- Navigation: arrow keys, j/k, Enter to inspect, q/Esc to quit
- Scrolling: viewport adjusts when selection moves beyond visible area

### Zig 0.16 API notes

- `std.ArrayList(T)` is unmanaged — pass allocator to `append(gpa, ...)` and `deinit(gpa)`
- Initialize with `.empty` instead of `.init(gpa)`
- `std.StringHashMap` still uses `.init(gpa)` and `.deinit()` (managed)
- Main signature: `pub fn main(init: std.process.Init) !void`
- Args: `init.minimal.args` -> `std.process.Args.Iterator.init()`
- Process spawn: `std.process.spawn(io, .{ .argv = &.{...} })`
- Dir stat: `d.statFile(io, name, .{})` (3 args after self)
- `posix.winsize` fields: `.row`, `.col`, `.xpixel`, `.ypixel`
