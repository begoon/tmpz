include .env
export
include .env-hosting
export

all:

NOW=$(shell date +'%Y-%m-%d@%H:%M:%S')

run-async:
	uvicorn main_async:listener --host 0.0.0.0 --port 8000 --reload

run-sync:
	PYTHONPATH=./package \
	flask -A main_sync:listener run -p 8000 -h 0.0.0.0 --reload

deps:
	-rm -rf package
	pip install --target ./package python-telegram-bot==13.15 ping3=4.0.8

health:
	curl $(HOSTING)/health

aws-pack: deps
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
	--environment "Variables={BOT_TOKEN=$(BOT_TOKEN),ADMIN=$(ADMIN),WH=$(HOSTING),WHERE=aws,UPDATED_AT=`date +'%Y-%m-%d %H:%M:%S'`}" \
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
	--set-env-vars=BOT_TOKEN=$(BOT_TOKEN),ADMIN=$(ADMIN),WH=$(HOSTING),UPDATED_AT=$(NOW),WHERE=gcp \
	--trigger-http

az-pack: deps
	rm -f bot_package.zip
	cp ./azure_function.py ./package/function_app.py
	cp ./host.json ./package
	cp ./bot_sync.py ./package
	(cd package && zip -r ../bot_package.zip .) 

az-deploy: az-pack
	az functionapp deployment source config-zip \
	-g Services \
	-n bot-function \
	--src bot_package.zip

az-settings:
	az functionapp config appsettings list \
	--name bot-function \
	--resource-group Services \

az-configure:
	az functionapp config appsettings set \
	--name bot-function \
	--resource-group Services \
	--settings \
	BOT_TOKEN=$(BOT_TOKEN) \
	ADMIN=$(ADMIN) \
	WH=$(HOSTING) \
	WHERE=azure \
	UPDATED_AT=$(NOW) \
