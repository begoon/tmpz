all:
	@echo "Usage: make [swift|rust|go|deno|bun|zig|ruby|dart|php|python|q|clean]"

swift:
	swift build && swift run http-server

rust:
	cargo run -p http-server

go:
	go run main.go

deno:
	deno run -A --watch main-deno.ts

bun:
	bun run main-bun.ts

zig:
	zig run main.zig

ruby:
	ruby main.rb

dart:
	dart main.dart

php:
	php -S localhost:8000 main.php

python:
	fastapi dev main.py

q:
	curl -q http://localhost:8000/version

clean:
	-rm -rf .build
	cargo clean
