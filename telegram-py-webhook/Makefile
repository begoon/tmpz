include .env
export
include .env-hosting
export

all:

run:
	uvicorn main:listener --host 0.0.0.0 --port 8000 --reload

deps:
	pip install --target ./package python-telegram-bot 

pack:
	rm -f bot_package.zip
	cp ./lambda_function.py ./package
	cp ./bot.py ./package
	(cd package && zip -r ../bot_package.zip .) 

aws-deploy: pack
	aws lambda update-function-code \
	--profile $(AWS_PROFILE) \
	--function-name bot \
	--zip-file fileb://bot_package.zip \
	--no-cli-pager

aws-configure:
	aws lambda update-function-configuration \
	--profile $(AWS_PROFILE) \
	--function-name bot \
	--environment "Variables={BOT_TOKEN=$(BOT_TOKEN),ADMIN=$(ADMIN),UPDATED_AT=`date +'%Y-%m-%d %H:%M:%S'`}" \
	--no-cli-pager

aws-health:
	curl $(HOSTING)/health
