all:

build:
	go generate
	go build -o ./exe main.go

dev:
	air \
	--build.cmd "make build" \
	--build.bin "./exe" \
	--build.include_ext "go,tpl,tmpl,html,css,js"

deploy:
	vercel deploy --prod
