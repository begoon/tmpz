include .env
export

all:

build:
	docker build -t $(LAMBDA_NAME) --platform=linux/amd64 .

tag-push:
	docker tag $(LAMBDA_NAME):latest $(REPO)/$(IMAGE):latest
	docker push $(REPO)/$(IMAGE):latest
	
last-tag:
	aws ecr batch-get-image \
	--profile $(AWS_PROFILE) \
	--repository-name $(IMAGE) \
	--image-ids imageTag=latest \
	| jq -e '.images[0].registryId + ".dkr.ecr.eu-west-2.amazonaws.com/" + .images[0].repositoryName + "@" + .images[0].imageId.imageDigest' | tr -d '"'

function-image:
	aws lambda get-function \
	--profile $(AWS_PROFILE) \
	--function-name $(LAMBDA_NAME) \
	| jq -r '.Code.ImageUri'

update:
	aws lambda update-function-code \
	--profile $(AWS_PROFILE) \
	--function-name $(LAMBDA_NAME) \
	--image-uri \
	$(shell aws ecr batch-get-image --profile $(AWS_PROFILE) --repository-name $(LAMBDA_NAME) --image-ids imageTag=latest | jq -e '.images[0].registryId + ".dkr.ecr.eu-west-2.amazonaws.com/" + .images[0].repositoryName + "@" + .images[0].imageId.imageDigest' | tr -d '"')

update-function:
	aws lambda update-function-code \
	--profile $(AWS_PROFILE) \
	--function-name $(LAMBDA_NAME) \
	--image-uri \
	$(shell aws lambda get-function --profile $(AWS_PROFILE) --function-name $(LAMBDA_NAME) | jq -r '.Code.ImageUri')
