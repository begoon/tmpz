module main

// Export an allocator so JS can reserve space in wasm memory when needed.
@[export: 'alloc']
pub fn alloc(n u32) &u8 {
	unsafe {
		return malloc(n)
	}
}

// Free a buffer that was allocated inside the module.
@[export: 'dealloc']
pub fn dealloc(p &u8) {
	unsafe { free(p) }
}

@[export: 'process']
pub fn process(in_ptr &u8, in_len u32) (&u32, u32) {
	unsafe {
		out_ptr := malloc(in_len)
		for i := 0; i < in_len; i++ {
			out_ptr[i] = u8(0x41 + i)
		}
		return out_ptr, u32(in_len)
	}
}
