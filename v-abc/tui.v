import term.ui as tui

struct App {
mut:
	tui &tui.Context = unsafe { nil }
}

fn event(e &tui.Event, x voidptr) {
	if e.typ == .key_down && e.code == .escape {
		exit(0)
	}
}

fn frame(x voidptr) {
	mut app := unsafe { &App(x) }

	app.tui.clear()
	app.tui.set_bg_color(r: 63, g: 81, b: 181)
	app.tui.draw_rect(20, 6, 41, 10)
	app.tui.draw_text(24, 8, 'Hello from V!')
	app.tui.set_cursor_position(0, 0)

	app.tui.reset()
	app.tui.flush()
}

fn main() {
	mut app := &App{}
	app.tui = tui.init(
		user_data:   app
		event_fn:    event
		frame_fn:    frame
		hide_cursor: true
	)
	app.tui.run()!
}
