GREEN=\033[0;32m
RED=\033[0;31m
BLUE=\033[0;34m
WHITE=\033[0;37m
END=\033[0m

include .env
export

all: run

build-amd64:
	make build GOOS=linux GOARCH=amd64

build:
	CGO_ENABLED=0 \
	go build \
	-o ./exe \
	-ldflags "-X 'main.SHA=$(shell git rev-parse --short HEAD)'" \
	main.go

run: build
	./exe

NAME=go-dns

docker-build: build-amd64
	docker build -t $(NAME) \
	-f Dockerfile \
	.

docker-tag-push:
	docker tag $(NAME):latest $(REPO)/$(NAME):latest
	docker push $(REPO)/$(NAME):latest

IMAGE=$(shell \
docker inspect --format='{{index .RepoDigests 0}}' $(REPO)/$(NAME):latest)

latest:
	@echo $(IMAGE)

host:
	@gcloud run services describe $(NAME) \
	--region $(REGION) --format="value(status.url)"

ping:
	@HOST=$(shell make host) && \
	echo "dialig $(WHITE)$$HOST$(END)" && curl $$HOST/z/$(cmd)

watch:
	@HOST=$(shell make host) && watch "http $$HOST/z/ping"

deploy: latest
	gcloud run deploy $(NAME) \
	--image=$(IMAGE) \
	--set-env-vars=GODEBUG=netdns=go+2 \
	--region=$(REGION) \
	--project=$(PROJECT)

release: docker-build docker-tag-push deploy

post:
	@HOST=$(shell make host) && \
	http POST $$HOST/action a=1 b=2

