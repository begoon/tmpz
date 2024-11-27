all: build

build:
	CGO_ENABLED=0 go build -ldflags "-s -w" -o ./fswalk main.go

folder?=github
re?=__pycache__

test:
	make && ./fswalk $(HOME)/$(folder) $(re)

clean:
	rm -f ./fswalk

install:
	cp ./fswalk $(HOME)/bin
