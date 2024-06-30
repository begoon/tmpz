include ../.env
export

FUNCTION_NAME=lambda-go

all: build zip upload pause call

build:
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 \
	go build -tags lambda.norpc -o bootstrap main.go

zip: build
	zip function.zip bootstrap

upload: zip
	aws lambda update-function-code \
	--function-name $(FUNCTION_NAME) \
	--zip-file fileb://function.zip | cat

pause:
	@echo "pausing to allow AWS to update the function"
	@sleep 3

host:
	@aws lambda get-function-url-config --function-name $(FUNCTION_NAME) \
	| jq -r .FunctionUrl

call:
	@HOST=$(shell make host) && \
	echo "calling $$HOST" && \
	http POST $$HOST/call a=1 b="message"
