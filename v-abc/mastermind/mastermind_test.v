module main

fn test_compare() {
	for t in [
		[1234, 1234, 4, 0],
		[1234, 4321, 0, 4],
		[1234, 5678, 0, 0],
		[1234, 1243, 2, 2],
		[1234, 1111, 1, 0],
		[1234, 2111, 0, 2],
	] {
		assert compare_1(t[0], t[1]) == Comparison{
			in_place: t[2]
			by_value: t[3]
		}, 'compare_1(${t[0]}, ${t[1]}) should be in_place: ${t[2]}, by_value: ${t[3]}'
		assert compare_2(t[0], t[1]) == Comparison{
			in_place: t[2]
			by_value: t[3]
		}, 'compare_2(${t[0]}, ${t[1]}) should be in_place: ${t[2]}, by_value: ${t[3]}'
	}
}

fn test_1_vs_2() {
	probes := create_universe()
	codes := create_universe()
	for code in codes {
		for probe in probes {
			assert compare_1(probe, code) == compare_2(probe, code), 'compare_1(${probe}, ${code}) != compare_2(${probe}, ${code})'
		}
	}
}
