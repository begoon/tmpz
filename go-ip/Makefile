all: build run

build:
	GCO_ENABLED=0 go build -o ./ip main.go

run:
	./ip

build-linux:
	GOOS=linux GOARCH=amd64 make build
	upx -9 ./ip