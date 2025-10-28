module main

struct Comparison {
mut:
	in_place int
	by_value int
}

struct Game {
mut:
	universe   []int
	candidates []int
	tries      int

	probe int

	eliminated int
	remaining  int
}

fn create_game() Game {
	return Game{
		universe:   create_universe()
		candidates: create_universe()
		tries:      0
		probe:      0
		eliminated: 0
		remaining:  1296
	}
}

// ---- Knuth minimax probe selection ----
fn (mut g Game) guess(in_place int, by_value int) int {
	if in_place == 4 {
		return 0
	}

	if g.probe != 0 {
		g.eliminate(g.probe, in_place, by_value)
	}

	if g.remaining == 0 {
		return -1
	}

	mut best_probe := 0
	mut min_rank := 0

	for probe in g.universe {
		probe_in_candidates := if probe in g.candidates { 1 } else { 0 }

		mut buckets := []int{len: 45, init: 0} // index = in_place*10 + by_value, max = 4*10 + 4 = 44
		mut worst_eval := -1

		for candidate in g.candidates {
			if candidate == 0 {
				continue // skipped eliminated candidates
			}
			cmp := compare_1(probe, candidate)
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

	g.probe = best_probe

	g.tries += 1
	return best_probe
}

fn (mut g Game) eliminate(probe int, in_place int, by_value int) {
	g.eliminated = 0
	g.remaining = 0

	// eliminate candidates not matching feedback
	for i, candidate in g.candidates {
		if candidate == 0 {
			continue // already eliminated
		}
		cmp := compare_1(probe, candidate)
		if cmp.in_place != in_place || cmp.by_value != by_value {
			g.candidates[i] = 0
			g.eliminated++
		} else {
			g.remaining++
		}
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
fn compare_1(probe int, code int) Comparison {
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
		p1 = -2
	}
	if p2 == c2 {
		cmp.in_place++
		c2 = -1
		p2 = -2
	}
	if p3 == c3 {
		cmp.in_place++
		c3 = -1
		p3 = -2
	}
	if p4 == c4 {
		cmp.in_place++
		c4 = -1
		p4 = -2
	}

	// by-value
	if p1 == c2 {
		cmp.by_value++
		c2 = -1
		p1 = -2
	} else if p1 == c3 {
		cmp.by_value++
		c3 = -1
		p1 = -2
	} else if p1 == c4 {
		cmp.by_value++
		c4 = -1
		p1 = -2
	}

	if p2 == c1 {
		cmp.by_value++
		c1 = -1
		p2 = -2
	} else if p2 == c3 {
		cmp.by_value++
		c3 = -1
		p2 = -2
	} else if p2 == c4 {
		cmp.by_value++
		c4 = -1
		p2 = -2
	}

	if p3 == c1 {
		cmp.by_value++
		c1 = -1
		p3 = -2
	} else if p3 == c2 {
		cmp.by_value++
		c2 = -1
		p3 = -2
	} else if p3 == c4 {
		cmp.by_value++
		c4 = -1
		p3 = -2
	}

	if p4 == c1 {
		cmp.by_value++
		c1 = -1
		p4 = -2
	} else if p4 == c2 {
		cmp.by_value++
		c2 = -1
		p4 = -2
	} else if p4 == c3 {
		cmp.by_value++
		c3 = -1
		p4 = -2
	}

	return cmp
}

// compare a probe against a code, returning <in_place, by_value>
fn compare_2(probe int, code int) Comparison {
	// extract 4 digits (thousands → ones)
	mut p := [probe / 1000 % 10, probe / 100 % 10, probe / 10 % 10, probe % 10]
	mut c := [code / 1000 % 10, code / 100 % 10, code / 10 % 10, code % 10]

	mut in_place := 0
	mut by_value := 0

	// count unmatched code digits
	mut freq := map[int]int{}

	// pass 1: exact matches; build freq for remaining code digits
	for i, cv in c {
		if p[i] == cv {
			in_place++
		} else {
			freq[cv]++
		}
	}

	// pass 2: value-only matches using remaining frequencies
	for i, pv in p {
		if pv == c[i] { // already counted as in_place
			continue
		}
		if freq[pv] > 0 {
			by_value++
			freq[pv]--
		}
	}

	return Comparison{
		in_place: in_place
		by_value: by_value
	}
}
