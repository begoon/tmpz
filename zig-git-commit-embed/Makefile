all: run

run:
	zig build -Dgit-commit=$(shell git rev-parse --short HEAD) run

clean:
	-rm -rf zig-out ./zig-cache
