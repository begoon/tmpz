import json
import os
import pathlib
import sys

import redis
import telegram

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN = os.environ["ADMIN"]

bot = telegram.Bot(BOT_TOKEN)

r = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
)

name = sys.argv[1]
content = open(name, "rb") if pathlib.Path(name).exists() else name
result = bot.send_photo(ADMIN, content)
print(json.dumps(result.to_dict(), indent=2))

if isinstance(content, str):
    photo = result.photo[-1]
    photo_dict = photo.to_dict()
    photo_dict["type"] = "photo"
    photo_dict_str = json.dumps(photo_dict)
    r.set("files:" + photo.file_id, photo_dict_str)
