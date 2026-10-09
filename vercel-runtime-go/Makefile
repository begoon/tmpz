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

README_URL = https://raw.githubusercontent.com/begoon/begoon/main/README.md

vendor-readme:
	curl -fsSL $(README_URL) -o internal/web/content/README.md
	git --no-pager diff --stat internal/web/content/README.md
