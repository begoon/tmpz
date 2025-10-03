fn main() {
	a := 69
	f := fn [a] () string {
		println('inside f() | a = ${a}')
		return '123'
	}
	f()
	println('hello [${f()}], V!')
	println(xx())
	yy := xx() + '|' + xx() + '|' + int(10).str()
	println(yy)
}

fn xx() string {
	return 'xx-123'
}
