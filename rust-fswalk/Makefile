all: run

run:
	cargo run

release:
	cargo build --release
	mv target/release/rust-fswalk ./main

clean:
	cargo clean
	rm -f ./main
