all: build

# https://depth-first.com/articles/2019/10/16/compiling-c-to-webassembly-and-running-it-without-emscripten/

build:
	clang \
	--target=wasm32 \
	--no-standard-libraries \
	-Wl,--export-all -Wl,--no-entry \
	-o main.wasm \
	main.c

prerequisities-mac:
	brew install llvm
	@echo -
	@echo "NOTE: add the following to your ~/.zshrc or ~/.bashrc"
	@echo -
	@echo "export PATH=/opt/homebrew/opt/llvm/bin:\$$PATH"
	@echo -
	@echo "and check that 'llc' is in your path by running"
	@echo -
	@echo "llc --version | grep wasm"
