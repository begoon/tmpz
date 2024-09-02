all: build run

build:
	bun build --compile --outfile ./exe main.ts ./public/**

run:
	./exe

dev:
	bun run --watch ./main.ts ./public/**
