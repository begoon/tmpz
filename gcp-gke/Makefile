include .env
export 

dev:
	deno run -A --watch info.ts

docker-build:
	docker build -t $(INFO_IMAGE) --platform linux/amd64 .

docker-tag-push:
	test -n "$(TAG)" || (echo "TAG is not set" && exit 1)
	docker tag $(INFO_IMAGE) $(REPO)/$(INFO_IMAGE):$(TAG)
	docker push $(REPO)/$(INFO_IMAGE):$(TAG)

build-tag-push: docker-build docker-tag-push

kubectl-create-deployment:
	test -n "$(TAG)" || (echo "TAG is not set" && exit 1)
	kubectl create deployment info-service \
	--image $(REPO)/$(INFO_IMAGE):$(TAG)

info-lb-public-ip:
	@kubectl get services info-loadbalancer \
	--output jsonpath='{.status.loadBalancer.ingress[0].ip}'

ingress-public-ip:
	@kubectl get ingress \
	--output jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'

watch:
	watch -n 1 "$(MAKE) info"

info:
	make pods
	@echo
	@echo $(shell make info-lb-public-ip)
	@curl -s http://$(shell make info-lb-public-ip) | jq '.HOSTNAME, .VERSION, .GENERATION'
	@curl -s http://$(shell make info-lb-public-ip)/shared?h=timer-job
	@echo
	@echo http://$(shell make ingress-public-ip)/info
	@curl -s http://$(shell make ingress-public-ip)/info | jq '.HOSTNAME, .VERSION, .GENERATION'
	@echo
	@echo http://$(shell make ingress-public-ip)/web
	@http -h http://$(shell make ingress-public-ip)/web | grep -i "caddy"

pods:
	kubectl get pods

probe:
	@curl -s http://$(shell make info-lb-public-ip)/probe?h=$(TARGET)

probe-caddy:
	make probe TARGET=http://caddy
