include .env
export 

TUNNEL=$(shell curl -s http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url')

dev:
	deno run -A --watch index.ts

publish:
	test -n "$(MSG)" || (echo "MSG is not set" && exit 1)
	gcloud pubsub topics publish \
	projects/iproov-chiro/topics/channel$(DLQ) \
	--message "$(MSG)"

tunnel:
	grok http 8000

tf-apply:
	terraform apply

tf-destroy:
	terraform destroy
