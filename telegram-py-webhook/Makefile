include .env
export
include .env-hosting
export

all:

NOW=$(shell date +'%Y-%m-%d@%H:%M:%S')

run:
	uvicorn main:listener --host 0.0.0.0 --port 8000 --reload

run-sync:
	PYTHONPATH=./package \
	flask -A main_sync:listener run -p 8000 -h 0.0.0.0 --reload

deps:
	-rm -rf package
	pip install --target ./package python-telegram-bot==13.15

health:
	curl $(HOSTING)/health

aws-pack:
	rm -f bot_package.zip
	cp ./lambda_function.py ./package
	cp ./bot_sync.py ./package
	(cd package && zip -r ../bot_package.zip .) 

aws-deploy: aws-pack
	aws lambda update-function-code \
	--profile $(AWS_PROFILE) \
	--function-name bot \
	--zip-file fileb://bot_package.zip \
	--no-cli-pager

aws-configure:
	aws lambda update-function-configuration \
	--profile $(AWS_PROFILE) \
	--function-name bot \
	--environment "Variables={BOT_TOKEN=$(BOT_TOKEN),ADMIN=$(ADMIN),WH=$(HOSTING),UPDATED_AT=`date +'%Y-%m-%d %H:%M:%S'`}" \
	--no-cli-pager

gcp-pack:
	-rm -rf cloud_function
	mkdir cloud_function
	cp cloud_function.py cloud_function/main.py
	cp bot_sync.py requirements.txt cloud_function/


gcp-deploy: gcp-pack
	gcloud functions deploy bot \
	--project $(GCP_PROJECT) \
	--gen2 \
	--region=europe-west2 \
	--runtime=python311 \
	--source=./cloud_function \
	--entry-point=function_handler \
	--set-env-vars=BOT_TOKEN=$(BOT_TOKEN),ADMIN=$(ADMIN),WH=$(HOSTING),UPDATED_AT=$(NOW) \
	--trigger-http
