include ../.env
export

all:

zip:
	chmod 755 function.sh bootstrap
	zip function.zip function.sh bootstrap

FUNCTION_NAME=shell-lambda

all: zip upload pause call

upload: zip
	aws lambda update-function-code \
	--function-name $(FUNCTION_NAME) \
	--zip-file fileb://function.zip | cat

pause:
	@echo "wait a moment for AWS to update the function and press any key"
	@sleep 0

host:
	@aws lambda get-function-url-config --function-name $(FUNCTION_NAME) \
	| jq -r .FunctionUrl

call:
	@HOST=$(shell make host) && \
	echo "calling $$HOST" && \
	http POST $$HOST/call a=1 b="message"
