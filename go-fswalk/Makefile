all: 

release:
	CGO_ENABLED=0 \
	go build -ldflags "-s -w" -o ./main main.go

clean:
	rm -f ./main
