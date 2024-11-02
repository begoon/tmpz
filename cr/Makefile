all: build install

build: build-cr build-vm

install: install-cr install-vm

build-cr:
	bun build ./cr.ts --compile --outfile=cr

install-cr:
	cp cr $(HOME)/bin

build-vm:
	bun build ./vm.ts --compile --outfile=vm

install-vm:
	cp vm $(HOME)/bin
