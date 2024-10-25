all: tw run

tw:
	tailwindcss -m -i tw.css -o styles.css $(WATCH)

tw-watch:
	make tw WATCH=--watch

run:
	python -m http.server
