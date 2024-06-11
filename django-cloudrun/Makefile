all:

include .env
export

VERSION=$(shell poetry version --short)
SHA=$(shell git rev-parse --short HEAD)
NOW=$(shell date +'%Y%m%d%H%M%S')

TAG=$(VERSION)-$(SHA)

URL=$(shell \
	gcloud run services list \
	--format="value(status.address.url)" \
	--filter=$(IMAGE))

info:
	@echo IMAGE=$(IMAGE)
	@echo REPO=$(REPO)
	@echo VERSION=$(VERSION)
	@echo TAG=$(TAG)
	@echo URL=$(URL)

build:
	./manage.py collectstatic --noinput
	docker build -t $(IMAGE) $(PLATFORM) .

build-amd64:
	$(MAKE) build PLATFORM="--platform=linux/amd64"

tag-push:
	docker tag $(IMAGE) $(REPO)/$(IMAGE):$(TAG)
	docker push $(REPO)/$(IMAGE):$(TAG)

restart:
	gcloud run deploy $(IMAGE) \
	--image=$(REPO)/$(IMAGE):$(TAG) \
	--allow-unauthenticated \
	--port=8080 \
	--service-account=$(SERVICE_ACCOUNT) \
	--max-instances=1 \
	--execution-environment=gen2 \
	--set-cloudsql-instances=$(CLOUD_SQL_INSTANCE) \
	--set-env-vars=DATABASE_URL=$(DATABASE_URL) \
	--set-env-vars=DJANGO_SECRET_KEY=$(DJANGO_SECRET_KEY) \
	--set-env-vars=TAG=$(TAG) \
	--set-env-vars=UPDATED_AT=$(NOW) \
	--set-env-vars=BOT_TOKEN=$(BOT_TOKEN) \
	--set-env-vars=WHEEL=$(WHEEL) \
	--set-env-vars=TELEGRAM_SECRET_TOKEN=$(TELEGRAM_SECRET_TOKEN) \
	--set-env-vars=WHERE=django \
	--region=$(REGION) \
	--project=$(PROJECT)

health:
	curl -s $(URL)/health | jq

env:
	curl -s $(URL)/update/env | jq

pipeline:
	make build-amd64 tag-push restart health

run-docker:
	docker run -it --rm -p 8000:8000 --env-file .env $(IMAGE)

run-dev:
	./manage.py runserver

run-uvicorn:
	uvicorn application.asgi:application --reload
