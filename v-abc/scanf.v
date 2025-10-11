module main

fn main() {
	mut a := 0
	mut b := 0
	print('enter a number: ')
	unsafe { C.scanf(c'%d %d', &a, &b) }
	println('you entered: ${a} and ${b}')
}
