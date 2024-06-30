include ../.env
export

FUNCTION_NAME=lambda-ts

all: zip upload pause call

build:
	@rm -rf .deno_cache/*
	DENO_DIR=$(PWD)/.deno_cache \
	deno cache \
	--lock "$(PWD)/deno.lock" \
	*.ts

zip: build
	chmod 755 bootstrap
	rm -f function.zip
	zip -r function.zip bootstrap \
		deno.lock .deno_cache/* \
		*.ts
	unzip -l function.zip
	ls -al function.zip

upload: zip
	aws lambda update-function-code \
	--function-name $(FUNCTION_NAME) \
	--zip-file fileb://function.zip | cat

pause:
	@echo "wait a moment for AWS to update the function..."
	@sleep 3

host:
	@aws lambda get-function-url-config --function-name $(FUNCTION_NAME) \
	| jq -r .FunctionUrl

call:
	@HOST=$(shell make host) && \
	echo "calling $$HOST" && \
	http POST $$HOST/call a=1 b="message"
