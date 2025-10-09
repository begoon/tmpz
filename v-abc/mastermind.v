module main

import os

struct Comparison {
mut:
	in_place int
	by_value int
}

fn main() {
	mut universe := create_universe()
	mut candidates := create_universe()

	mut tries := 1
	for {
		// ---- Knuth minimax probe selection ----
		mut best_probe := 0
		mut min_rank := 0

		for probe in universe {
			probe_in_candidates := if probe in candidates { 1 } else { 0 }

			mut buckets := []int{len: 45, init: 0} // index = in_place*10 + by_value, max = 4*10 + 4 = 44
			mut worst_eval := -1

			for candidate in candidates {
				if candidate == 0 {
					continue // skipped eliminated candidates
				}
				cmp := compare(probe, candidate)
				valuation := cmp.in_place * 10 + cmp.by_value
				buckets[valuation] += 1
				if buckets[valuation] > worst_eval {
					worst_eval = buckets[valuation]
				}
			}

			// rank = probe (1111..6666) + (not in candidates)*10000 + worst_eval*100000
			rank := probe + (1 - probe_in_candidates) * 10000 + worst_eval * 100000
			if min_rank == 0 || rank < min_rank {
				min_rank = rank
				best_probe = probe
			}
		}

		println('\nmaybe ${best_probe} ? ')
		print('#${tries}, enter feedback, <in-place> and <by-value> (e.g. "1 2"): ')

		mut in_place := 0
		mut by_value := 0
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

		if in_place == 4 {
			println('\nguesses in ${tries} tries')
			break
		}

		mut eliminated := 0
		mut remaining := 0

		print('\n')

		// eliminate candidates not matching feedback
		for i, candidate in candidates {
			if candidate == 0 {
				continue // already eliminated
			}
			cmp := compare(best_probe, candidate)
			if cmp.in_place != in_place || cmp.by_value != by_value {
				candidates[i] = 0
				eliminated++
			} else {
				remaining++
				print('${candidate} ')
			}
		}
		println('\n${eliminated} candidates eliminated, ${remaining} remaining')

		if remaining == 0 {
			println('no candidates remaining, it is impossible!')
			break
		}

		tries += 1
	}
}

// build the universe: integers 1111..6666 with base-6 digits (1..6)
fn create_universe() []int {
	mut universe := []int{len: 1296, init: 0}
	mut off := 0
	for i in 0 .. 6 {
		for j in 0 .. 6 {
			for k in 0 .. 6 {
				for l in 0 .. 6 {
					v := i * 1000 + j * 100 + k * 10 + l + 1111
					universe[off] = v
					off++
				}
			}
		}
	}
	return universe
}

// compare a probe against a code, returning <in_place, by_value>
fn compare(probe int, code int) Comparison {
	mut p1 := (probe / 1000) % 10
	mut p2 := (probe / 100) % 10
	mut p3 := (probe / 10) % 10
	mut p4 := probe % 10

	mut c1 := (code / 1000) % 10
	mut c2 := (code / 100) % 10
	mut c3 := (code / 10) % 10
	mut c4 := code % 10

	mut cmp := Comparison{
		in_place: 0
		by_value: 0
	}

	// in-place
	if p1 == c1 {
		cmp.in_place++
		c1 = -1
	}
	if p2 == c2 {
		cmp.in_place++
		c2 = -1
	}
	if p3 == c3 {
		cmp.in_place++
		c3 = -1
	}
	if p4 == c4 {
		cmp.in_place++
		c4 = -1
	}

	// by-value
	if p1 == c2 {
		cmp.by_value++
		c2 = -1
	} else if p1 == c3 {
		cmp.by_value++
		c3 = -1
	} else if p1 == c4 {
		cmp.by_value++
		c4 = -1
	}

	if p2 == c1 {
		cmp.by_value++
		c1 = -1
	} else if p2 == c3 {
		cmp.by_value++
		c3 = -1
	} else if p2 == c4 {
		cmp.by_value++
		c4 = -1
	}

	if p3 == c1 {
		cmp.by_value++
		c1 = -1
	} else if p3 == c2 {
		cmp.by_value++
		c2 = -1
	} else if p3 == c4 {
		cmp.by_value++
		c4 = -1
	}

	if p4 == c1 {
		cmp.by_value++
		c1 = -1
	} else if p4 == c2 {
		cmp.by_value++
		c2 = -1
	} else if p4 == c3 {
		cmp.by_value++
		c3 = -1
	}

	return cmp
}
