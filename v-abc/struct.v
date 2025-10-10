struct Abc {
	s string
}

fn main() {
	a := &Abc{'abc'}
	defer { unsafe { a.free() } }
	println(a)
}
