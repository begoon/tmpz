include .env
export

all:

test:
	curl \
	-H 'Content-Type: application/json' \
	-d '{"contents":[{"parts":[{"text":"Explain how AI works"}]}]}' \
	-X POST 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${GEMINI_API_KEY}'
