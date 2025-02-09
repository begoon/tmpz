default: build

set unstable := true
set dotenv-load := true

NAME := env('NAME', "cloudrun-stub")
REPO := env('REPO', "UNDEFINED")
TAG := env('TAG', datetime("%Y%m%d%H%M%S"))

build:
    go build -o ./exe .

build-amd64:
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o ./exe .

docker-build:
    docker build -t {{ NAME }} .

docker-build-amd64:
    docker build --platform linux/amd64 -t {{ NAME }} .

docker-run:
    docker run --rm -it -p :8000:8000 {{ NAME }}

docker-tag-push:
    docker tag {{ NAME }}:latest {{ REPO }}/{{ NAME }}:{{ TAG }}
    docker push {{ REPO }}/{{ NAME }}:{{ TAG }}

docker-release: build-amd64 docker-build-amd64 docker-tag-push

promote:
    #!/bin/bash
    gcloud run deploy stubbed \
    --image={{ REPO }}/{{ NAME }}:{{ TAG }} \
    --allow-unauthenticated \
    --port=8000 \
    --min-instances=0 \
    --max-instances=1 \
    --memory=512Mi \
    --cpu=1 \
    --ingress=all \
    --execution-environment=gen2 \
    --region=europe-west2 \
    --project=iproov-chiro \
    --set-env-vars=INITIAL=1

clean:
    rm -f ./exe
