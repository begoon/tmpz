all: build

build:
	cargo build --release
	mv target/release/fswalk .

folder?=github
re?=__pycache__

test:
	make && ./fswalk $(HOME)/$(folder) $(re)

install:
	cp ./fswalk $(HOME)/bin

clean:
	cargo clean
	rm -f ./fswalk
