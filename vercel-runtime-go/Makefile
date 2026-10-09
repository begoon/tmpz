all:

build:
	go build -o ./exe .

dev:
	air \
	--build.cmd "make build" \
	--build.bin "./exe" \
	--build.include_ext "go,tpl,tmpl,html,css,js"

deploy:
	vercel deploy --prod
