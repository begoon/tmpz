module main;
import std::io;
import std::os;
import std::time;
import std::thread;

const String[] ANSI_COLORS = {
    "\x1b[91m", // bright red
    "\x1b[92m", // bright green
    "\x1b[93m", // bright yellow
    "\x1b[94m", // bright blue
    "\x1b[95m", // bright magenta
    "\x1b[96m", // bright cyan
    "\x1b[97m"  // bright white
};

const String ANSI_RESET = "\x1b[0m";

fn int main(String[] args)
{
    Clock now = time::clock::now();
    io::printn(now);

    io::printn(os::env::get_var("HOME"))!!;
    if (catch io::printn(os::env::get_var("TERM"))) {
        io::printn("TERM not found");
        return 1;
    }

    defer {
        std::thread::sleep_ms(345);
        io::printn("finale");
        io::printfn("%s%s%s\n", ANSI_COLORS[2], now.to_now(), ANSI_RESET);
    }

    foreach (i, v: args)
    {
        io::printf("%d:%s<%s>%s ", i, ANSI_COLORS[i % ANSI_COLORS.len], v, ANSI_RESET);
    }
    io::printn("");
    return 0;
}
