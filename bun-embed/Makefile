all: build run

build:
	bun build --compile ./main.ts ./files/*.html --outfile exe

run:
	./exe

test:
	echo "INDEX-1" > ./files/index.html
	ls -l ./files/*
	hexdump -C ./files/*
	bun build --compile ./main.ts ./files/*.html --outfile exe1
	#
	echo "INDEX-2" > ./files/index.html
	ls -l ./files/*
	hexdump -C ./files/*
	bun build --compile ./main.ts ./files/*.html --outfile exe2
	#
	ls -al exe*
	#
	xxd exe1 > exe1.hex
	xxd exe2 > exe2.hex
	diff exe1.hex exe2.hex

build-x:
	bun build --compile --outfile ./exe main-x.ts ./public/**

dev:
	bun run --watch ./main.ts ./public/**

clean:
	rm -f exe*
