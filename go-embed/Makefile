all: build run

build:
	go build -o ./exe

run:
	./exe

test:
	-mkdir files
	#
	echo "INDEX-1" > files/index.html
	ls -al files/*
	hexdump files/*
	go build -o ./exe1
	#
	echo "INDEX-2" > files/index.html
	ls -al files/*
	hexdump files/*
	go build -o ./exe2
	#
	ls -al exe*
	#
	xxd exe1 > exe1.hex
	xxd exe2 > exe2.hex
	diff exe1.hex exe2.hex

clean:
	-rm exe*
