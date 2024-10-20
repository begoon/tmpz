all:

build:
	go build -o ./exe main.go

dev:
	air -d \
	--build.cmd "go build -o ./exe main.go" \
	--build.bin "./exe" \
	--build.include_ext "go,tpl,tmpl,html,css,js"

deploy:
	vercel deploy --prod
