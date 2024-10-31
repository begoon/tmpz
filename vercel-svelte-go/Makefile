all:

COMMIT := $(shell git rev-parse --short HEAD)
export COMMIT

build:
	bun run build
	go build -o ./exe main.go

dev:
	air \
	--build.cmd "make build" \
	--build.bin "./exe" \
	--build.include_ext "go,tpl,tmpl,html,css,ts,js,svelte" \
	--build.include_file "Makefile" \
	--build.include_file "Justfile" \
	--build.exclude_dir "node_modules,api/static" \

dev-vite:
	bun run build:watch

deploy:
	vercel deploy --prod
