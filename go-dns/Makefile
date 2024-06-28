include .env
export

all: run

build-amd64:
	make build GOOS=linux GOARCH=amd64

build:
	CGO_ENABLED=0 \
	go build -o ./exe main.go

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

ping:
	@HOST=$(shell \
	gcloud run services describe $(NAME) \
	--region $(REGION) --format="value(status.url)") && \
	echo "dialig $$HOST" && \
	curl $$HOST/$(cmd)


deploy: latest
	gcloud run deploy $(NAME) \
	--image=$(IMAGE) \
	--set-env-vars=GODEBUG=netdns=go+1 \
	--region=$(REGION) \
	--project=$(PROJECT)