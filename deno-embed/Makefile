all: build run

build:
	deno compile -A --include files -o ./exe main.ts

run:
	./exe

test:
	echo "INDEX-1" > ./files/index.html
	ls -l ./files/*
	hexdump -C ./files/*
	deno compile -A --include files -o ./exe1 main.ts
	#
	echo "INDEX-2" > ./files/index.html
	ls -l ./files/*
	hexdump -C ./files/*
	deno compile -A --include files -o ./exe2 main.ts
	#
	ls -al exe*
	#
	#
	xxd exe1 > exe1.hex
	xxd exe2 > exe2.hex
	diff exe1.hex exe2.hex

clean:
	rm -f exe*
