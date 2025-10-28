module main

import os

fn main() {
	mut game := create_game()

	mut in_place := -1
	mut by_value := -1

	for {
		probe := game.guess(in_place, by_value)
		if probe == 0 {
			println('game over in ${game.tries} guesses')
			break
		}
		if probe == -1 {
			println('no candidates remaining, it is impossible!')
			break
		}

		println('\nmaybe ${probe} ? ')
		print('#${game.tries}, enter feedback, <in-place> and <by-value> (e.g. "1 2"): ')

		for {
			line := os.input('> ').trim_space()
			if line.len == 0 {
				continue
			}
			parts := line.replace(',', ' ').split(' ').filter(it.len > 0)
			if parts.len == 2 {
				in_place = parts[0].int()
				by_value = parts[1].int()
				break
			}
			println('please enter two integers like "2 1"')
		}
	}
}
