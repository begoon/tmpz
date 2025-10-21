struct RefStruct {
mut:
	r &MyStruct
}

// see discussion below
@[heap]
struct MyStruct {
	n int
}

fn main() {
	mut m := MyStruct{}
	mut r := RefStruct{
		r: &m
	}
	r.g()
	println('r: ${r}')
}

fn (mut r RefStruct) g() {
	s := MyStruct{
		n: 7
	}
	r.f(&s) // reference to `s` inside `r` is passed back to `main() `
}

fn (mut r RefStruct) f(s &MyStruct) {
	r.r = s // would trigger error without `[heap]`
}
