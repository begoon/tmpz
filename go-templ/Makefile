all:

build:
	templ fmt *.templ
	templ generate
	tailwindcss -i css.css -o static/styles.css
	go build -o main .

dev:
	air -c .air.toml
