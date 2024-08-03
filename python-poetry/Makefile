all: build run ls

build:
	docker build -t poetry-env .

run:
	docker run -it --rm poetry-env $(CMD)

ls:
	docker image ls | head