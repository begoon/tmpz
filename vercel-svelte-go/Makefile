all:

build:
	go build -o ./exe main.go

dev:
	air \
	--build.cmd "make build" \
	--build.bin "./exe" \
	--build.include_ext "go,tpl,tmpl,html,css,js" \
	--build.exclude_dir "node_modules" 

deploy:
	vercel deploy --prod
