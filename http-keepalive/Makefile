all:

server:
	uvicorn main:application --timeout-keep-alive=1 --reload --log-level=trace

test:
	deno run -A client.ts 

test-paused:
	PAUSE=2000 deno run -A client.ts