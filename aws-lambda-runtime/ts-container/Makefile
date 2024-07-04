include .env
export

FUNCTION_NAME=lambda-ts-container

RUNTIME?=deno

all:

create-repo:
	aws ecr create-repository \
	--profile $(AWS_PROFILE) \
	--repository-name $(FUNCTION_NAME)

create-repo-retention-policy:
	aws ecr put-lifecycle-policy \
	--profile $(AWS_PROFILE) \
	--repository-name $(FUNCTION_NAME) \
	--lifecycle-policy-text file://ecr-retention-policy.json
	
build-tag-push: build tag-push

build:
	docker build -t $(FUNCTION_NAME) --platform linux/amd64 \
	-f Dockerfile-$(RUNTIME) .

REPO = $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REPO)

tag-push:
	 docker tag $(FUNCTION_NAME):latest $(REPO)/$(FUNCTION_NAME):latest
	 docker push $(REPO)/$(FUNCTION_NAME):latest

last-tag:
	@docker inspect $(FUNCTION_NAME):latest \
	| jq -r '.[0].RepoDigests[0] \
	| split("@")[1]'

# lambda

create-lambda-role:
	aws iam create-role \
	--profile $(AWS_PROFILE) \
	--role-name $(FUNCTION_NAME)-role \
	--assume-role-policy-document \
	'{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
	aws iam attach-role-policy \
	--profile $(AWS_PROFILE)
	--role-name $(FUNCTION_NAME)-role \
	--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \

create-lambda:
	aws lambda create-function \
	--function-name $(FUNCTION_NAME) \
	--role arn:aws:iam::$(AWS_ACCOUNT):role/$(FUNCTION_NAME)-role \
	--package-type Image \
	--code ImageUri=$(REPO)/$(FUNCTION_NAME):latest \
	--architectures x86_64 \
	--profile $(AWS_PROFILE) | cat

create-lambda-url:
	aws lambda create-function-url-config \
	--profile $(AWS_PROFILE) \
	--function-name $(FUNCTION_NAME) \
	--auth-type NONE 

create-lambda-invoke-permission:
	aws lambda add-permission \
	--profile femosofia2022 \
	--function-name $(FUNCTION_NAME) \
	--action lambda:InvokeFunctionUrl \
	--statement-id FunctionURLAllowPublicAccess \
	--principal "*" \
	--function-url-auth-type NONE 

# lambda development cycle

deploy: build-tag-push update-image wait

update-image:
	SHA=$(shell make last-tag) && \
	echo "SHA=$(WHITE)$$SHA$(NC)" && \
	aws lambda update-function-code \
	--profile $(AWS_PROFILE) \
	--function-name $(FUNCTION_NAME) \
	--image $(REPO)/$(FUNCTION_NAME)@$$SHA \
	| jq -r '.CodeSha256'

status:
	@aws lambda get-function --function-name $(FUNCTION_NAME) \
	--profile $(AWS_PROFILE) \
	| jq -r .Configuration.LastUpdateStatus

wait:
	@while [ "$$(make status)" != "Successful" ]; do \
		echo "wait a moment for AWS to update the function..."; \
		sleep 10; \
	done
	@echo "lambda function update complete"

lambda-url:
	@aws lambda get-function-url-config --function-name $(FUNCTION_NAME) \
	| jq -r '.FunctionUrl | rtrimstr("/")'

# invoke

invoke: get put-json put-text

put-json:
	@HOST=$(shell make lambda-url) && \
	http -b PUT "$$HOST/call?q=1" a=1 b="message"

put-text:
	@HOST=$(shell make lambda-url) && \
	http -b PUT "$$HOST/call?q=1" --raw='plain data'

get:
	@HOST=$(shell make lambda-url) && \
	http GET "$$HOST/call?a=1"

get-418:
	@HOST=$(shell make lambda-url) && \
	http GET "$$HOST/call?a=1&status=418"

# test

test: deploy get get-418 put-json put-text
