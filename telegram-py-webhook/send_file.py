import json
import os
import pathlib
import sys
from mimetypes import MimeTypes

import redis
import telegram

mime = MimeTypes()

BOT_TOKEN = os.environ["BOT_TOKEN"]
WHEEL = os.environ["WHEEL"]

bot = telegram.Bot(BOT_TOKEN)

r = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
)

name = sys.argv[1]
mimetype, _ = mime.guess_type(name)
assert mimetype is not None, f"unknown mimetype '{name}'"

category, _ = mimetype.split("/")
print(mimetype, category)

content = open(name, "rb") if pathlib.Path(name).exists() else name

sender = {
    "image": bot.send_photo,
    "audio": bot.send_audio,
    "video": bot.send_video,
}.get(category, None)

if sender:
    kind = category
else:
    kind = "document"
    sender = bot.send_document

result = sender(WHEEL, content)
print(json.dumps(result.to_dict(), indent=2))

if not isinstance(content, str):
    if result.photo:
        photo = result.photo[-1]
        photo_dict = photo.to_dict()
        photo_dict["type"] = "photo"
        photo_dict_str = json.dumps(photo_dict)
        r.set("files:" + photo.file_id, photo_dict_str)
        print("photo", photo.file_id)
    elif result.audio:
        audio = result.audio
        audio_dict = audio.to_dict()
        audio_dict["type"] = "audio"
        audio_dict_str = json.dumps(audio_dict)
        r.set("files:" + audio.file_id, audio_dict_str)
        print("audio", audio.file_id)
    elif result.video:
        video = result.video
        video_dict = video.to_dict()
        video_dict["type"] = "video"
        video_dict_str = json.dumps(video_dict)
        r.set("files:" + video.file_id, video_dict_str)
        print("video", video.file_id)
    else:
        document = result.document
        document_dict = document.to_dict()
        document_dict["type"] = "document"
        document_dict_str = json.dumps(document_dict)
        r.set("files:" + document.file_id, document_dict_str)
        print("document", document.file_id)
