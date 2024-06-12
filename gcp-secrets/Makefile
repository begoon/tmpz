include .env
export

all:

dev:
	deno run -A index.ts --watch

build:
	docker build -t $(IMAGE) $(PLATFORM) .

build-amd64:
	$(MAKE) build PLATFORM="--platform linux/amd64"

run:
	docker run -it --rm -p :8000:8000 $(IMAGE)

tag-push:
	docker tag $(IMAGE) $(REPO)/$(IMAGE)
	docker push $(REPO)/$(IMAGE)
