all: build run

build:
	zig build-exe main.zig

linux-amd64: build-linux-amd64 pack

build-linux-amd64:
	zig build-exe \
	-target x86_64-linux-gnu \
	-O ReleaseSmall \
	-fstrip \
	-fsingle-threaded \
	--name main \
	main.zig

pack:
	upx --lzma --best main

run:
	./main

clean:
	-rm -f main main.o
