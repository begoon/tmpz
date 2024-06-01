import json

import bot as bot

bot.starter()


def lambda_handler(event, context):
    http = event["requestContext"]["http"]
    if http["method"] == "GET" and "/health" in http["path"]:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(bot.health()),
        }

    if http["method"] == "POST" and http["path"] == "/bot":
        body = json.loads(event["body"])
        bot.update(body)
        return {'statusCode': 200}

    return {"statusCode": 418, "body": "Ha?"}
