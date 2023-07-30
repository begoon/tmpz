all: build run

build:
	docker build -t docker-memory-test .

run:
	docker run \
	--restart=always \
	-it \
	--memory=512M \
	--memory-swap=512M \
	docker-memory-test ; echo $$?
