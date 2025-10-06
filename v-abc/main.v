struct Type {
	a int
	b string
}

fn main() {
	v := Type{
		a: 123
		b: 'hello'
	}
	println(v)
	a := [1, 2, 3, 4, 5]
	f := fn [a] () string {
		println('inside f() | a = ${a}')
		return '123'
	}
	println('abc [${f()}], V!')
	println(xx())
	yy := xx() + '|' + xx() + '|' + int(10).str()
	println(yy)
}

fn xx() string {
	return 'xx-123'
}
