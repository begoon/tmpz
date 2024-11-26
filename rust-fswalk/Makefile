all: run

run:
	cargo run

release:
	cargo build --release
	mv target/release/fswalk .

folder?=github
re?=__pycache__

test:
	make release && ./fswalk $(HOME)/$(folder) $(re)

clean:
	cargo clean
	rm -f ./fswalk
