all:

run:
	go run main.go

release:
	CGO_ENABLED=0 go build -ldflags="-w -s" main.go

clean:
	rm -f main
