abc: build

FLAGS = -O3

wasm:
	emcc -o qoi.wasm \
	--no-entry \
  	-s EXPORTED_FUNCTIONS=_qoi_render,_malloc,_free \
  	qoi_decode_wasm.c \
	 $(FLAGS) \

clean:
	rm -f qoi.wasm
