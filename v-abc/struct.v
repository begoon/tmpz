struct Abc {
	s string
}

fn (a &Abc) free() {
	println('freeing &Abc')
	unsafe { a.s.free() }
}

fn main() {
	print('GC is ' + if gc_is_enabled() { 'on' } else { 'off' } + '\n')
	print('gc_heap_usage(): ${gc_heap_usage()}\n')
	print('gc_memory_use(): ${gc_memory_use()}\n')
	a := &Abc{'abc'}
	print('gc_heap_usage(): ${gc_heap_usage()}\n')
	print('gc_memory_use(): ${gc_memory_use()}\n')
	// defer { unsafe { a.free() } }
	println(a)
	unsafe { a.free() }
	gc_collect()
	print('gc_heap_usage(): ${gc_heap_usage()}\n')
	print('gc_memory_use(): ${gc_memory_use()}\n')
}
