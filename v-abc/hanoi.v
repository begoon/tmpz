const num = 4

fn main() {
	hanoi(num, 1, 2, 3)
}

fn move(n int, a int, b int) int {
	println('move ${n} from ${a} to ${b}')
	return 0
}

fn hanoi(n int, a int, b int, c int) int {
	if n == 1 {
		move(1, a, c)
	} else {
		hanoi(n - 1, a, c, b)
		move(n, a, c)
		hanoi(n - 1, b, a, c)
	}
	return 0
}
