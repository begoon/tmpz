DENO_DIR=$(PWD)/.cache
export

run:
	deno run -A \
	--no-remote \
	--no-check \
	--no-lock \
	--cached-only \
	main.ts

vendor: clean
	deno cache --no-lock main.ts

info:
	deno info

clean:
	-rm -rf .cache
	-rm -rf node_modules
