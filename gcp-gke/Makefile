include .env
export 

dev:
	deno run -A --watch info.ts

docker-build:
	docker build -t $(INFO_IMAGE) --platform linux/amd64 .

TAG?=v1

docker-tag-push:
	docker tag $(INFO_IMAGE) $(REPO)/$(INFO_IMAGE):$(TAG)
	docker push $(REPO)/$(INFO_IMAGE):$(TAG)

kubectl-create-deployment:
	kubectl create deployment info-service \
	--image $(REPO)/$(INFO_IMAGE):$(TAG)

public-ip:
	kubectl get services info \
	--output jsonpath='{.status.loadBalancer.ingress[0].ip}'

watch:
	watch -n 1 "$(MAKE) info"

info:
	make pods
	@echo
	@curl -s http://$(shell make public-ip) | jq '.HOSTNAME, .VERSION'

pods:
	kubectl get pods