all: build

build:
	CGO_ENABLED=0 go build -ldflags "-s -w" -o ./fswalk main.go

build-amd64:
	GOOS=linux GOARCH=amd64 make build

folder?=github
re?=__pycache__

test:
	make && ./fswalk $(HOME)/$(folder) $(re)

install:
	cp ./fswalk $(HOME)/bin/fsclean

clean:
	rm -f ./fswalk
