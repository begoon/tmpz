all:

include .env
export

build:
	./manage.py collectstatic --noinput
	docker build -t $(IMAGE) $(PLATFORM) .

build-amd64:
	$(MAKE) build PLATFORM="--platform=linux/amd64"

tag-push:
	docker tag $(IMAGE) $(REPO)/$(IMAGE):latest
	docker push $(REPO)/$(IMAGE):latest

run-docker:
	docker run -it --rm -p 8000:8000 --env-file .env $(IMAGE)

run-dev:
	./manage.py runserver

run-uvicorn:
	uvicorn application.asgi:application --reload
