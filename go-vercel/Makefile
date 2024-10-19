all:

dev:
	air --build.cmd "go build -o ./exe main.go" --build.bin "./exe" --build.exclude_dir "templates,build"

deploy:
	vercel deploy --prod
