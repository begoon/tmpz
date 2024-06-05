include .env
export

all:

NOW=$(shell date +'%Y-%m-%d@%H:%M:%S')

TUNNEL=$(shell curl -s http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url')

tunnel:
	@echo $(TUNNEL)

tunnel-info:
	ngrok api tunnels list --api-key $(NGROK_API_KEY)
	
run:
	PYTHONPATH=./package \
	flask -A main:listener run \
	-p 8000 -h 0.0.0.0 \
	--reload \
	--extra-files wh.json

run_:
	PYTHONPATH=./package \
	flask -A main_:listener run \
	-p 8000 -h 0.0.0.0 \
	--reload

deps:
	-rm -rf package
	pip install --target ./package \
	python-telegram-bot==13.15 \
	redis==5.0.4
	make optimize

optimize:
	find ./package | grep -E "(/__pycache__|\.pyc|\.pyo)" | xargs rm -rf
	cd package && \
	rm -rf \
		*.dist-info *.pth \
		_distutils_hack setuptools pkg_resources \
		apscheduler cachetools pytz tornado \
		async_timeout tzlocal telegram/ext \
		six.py


health:
	curl $(HOSTING)/health

#

aws-health:
	curl $(AWS_HOSTING)/health

aws-pack: deps
	rm -f bot_package.zip
	cp ./function_aws.py ./package
	cp ./bot.py ./package
	cp -R ./asset ./package
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
	--environment "Variables={ \
		BOT_TOKEN=$(BOT_TOKEN), \
		TELEGRAM_SECRET_TOKEN=$(TELEGRAM_SECRET_TOKEN), \
		WHEEL=$(WHEEL), \
		WHERE=aws, \
		REDIS_HOST=$(REDIS_HOST), \
		REDIS_PORT=$(REDIS_PORT), \
		REDIS_PASSWORD=$(REDIS_PASSWORD), \
		UPDATED_AT=$(NOW) \
	}" \
	--no-cli-pager

aws-tf-cmd:
	cd tf/aws && terraform $(CMD) -var-file=../private.tfvars

aws-tf-plan:
	make aws-tf-cmd CMD=plan

aws-tf-apply:
	make aws-tf-cmd CMD=apply

aws-tf-destroy:
	make aws-tf-cmd CMD=destroy

# GCP

gcp-health:
	curl $(GCP_HOSTING)/health

gcp-pack: deps
	rm -f bot_package.zip
	cp ./function_gcp.py ./package/main.py
	cp ./bot.py ./package
	cp -R ./asset ./package
	(cd package && zip -r ../bot_package.zip .) 
	gsutil cp bot_package.zip gs://bot-function/

gcp-deploy: gcp-pack
	gcloud functions deploy bot \
	--project $(GCP_PROJECT) \
	--gen2 \
	--region=europe-west2 \
	--runtime=python311 \
	--source=gs://bot-function/bot_package.zip \
	--entry-point=function_handler \
	--set-env-vars=BOT_TOKEN=$(BOT_TOKEN) \
	--set-env-vars=TELEGRAM_SECRET_TOKEN=$(TELEGRAM_SECRET_TOKEN) \
	--set-env-vars=WHEEL=$(WHEEL) \
	--set-env-vars=WHERE=gcp \
	--set-env-vars=REDIS_HOST=$(REDIS_HOST) \
	--set-env-vars=REDIS_PORT=$(REDIS_PORT) \
	--set-env-vars=REDIS_PASSWORD=$(REDIS_PASSWORD) \
	--set-env-vars=UPDATED_AT=$(NOW) \
	--trigger-http

gcp-tf-cmd:
	cd tf/gcp && terraform $(CMD) -var-file=../private.tfvars

gcp-tf-plan:
	make gcp-tf-cmd CMD=plan

gcp-tf-apply:
	make gcp-tf-cmd CMD=apply

gcp-tf-destroy:
	make gcp-tf-cmd CMD=destroy

# Azure

az-health:
	curl $(AZ_HOSTING)/health

az-pack: deps
	rm -f bot_package.zip
	cp ./function_azure.py ./package/function_app.py
	cp ./host.json ./package
	cp ./bot.py ./package
	cp -R ./asset ./package
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
	TELEGRAM_SECRET_TOKEN=$(TELEGRAM_SECRET_TOKEN) \
	WHEEL=$(WHEEL) \
	WHERE=azure \
	REDIS_HOST=$(REDIS_HOST) \
	REDIS_PORT=$(REDIS_PORT) \
	REDIS_PASSWORD=$(REDIS_PASSWORD) \
	UPDATED_AT=$(NOW)

az-tf-cmd:
	cd tf/az && terraform $(CMD) -var-file=../private.tfvars

az-tf-plan:
	make az-tf-cmd CMD=plan

az-tf-apply:
	make az-tf-cmd CMD=apply

az-tf-destroy:
	make az-tf-cmd CMD=destroy
