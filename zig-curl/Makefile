default: build run

build:
	zig build-exe main.zig --library curl --library c $(pkg-config --cflags libcurl)

run:
	./main

clean:
	-rm -f main
	-rm -f *.o
