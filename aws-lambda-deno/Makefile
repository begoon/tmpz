all:

build:
	docker build -t karta-pdf --platform=linux/amd64 .

tag-push:
	docker tag karta-pdf:latest 593011665686.dkr.ecr.eu-west-2.amazonaws.com/karta-pdf:latest
	docker push 593011665686.dkr.ecr.eu-west-2.amazonaws.com/karta-pdf:latest
	
last-tag:
	aws ecr batch-get-image \
	--profile femosofia2022 \
	--repository-name karta-pdf \
	--image-ids imageTag=latest \
	| jq -e '.images[0].registryId + ".dkr.ecr.eu-west-2.amazonaws.com/" + .images[0].repositoryName + "@" + .images[0].imageId.imageDigest' | tr -d '"'

function-image:
	aws lambda get-function \
	--profile femosofia2022 \
	--function-name karta-pdf \
	| jq -r '.Code.ImageUri'

update:
	aws lambda update-function-code \
	--profile femosofia2022 \
	--function-name karta-pdf \
	--image-uri \
	$(shell aws ecr batch-get-image --profile femosofia2022 --repository-name karta-pdf --image-ids imageTag=latest | jq -e '.images[0].registryId + ".dkr.ecr.eu-west-2.amazonaws.com/" + .images[0].repositoryName + "@" + .images[0].imageId.imageDigest' | tr -d '"')

update-function:
	aws lambda update-function-code \
	--profile femosofia2022 \
	--function-name karta-pdf \
	--image-uri \
	$(shell aws lambda get-function --profile femosofia2022 --function-name karta-pdf | jq -r '.Code.ImageUri')
