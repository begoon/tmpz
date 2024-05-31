import json
import logging
import os
import pathlib
import random
from typing import Any, Callable, cast

import ping3
import redis
from telegram import (
    Bot,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)
from telegram.utils.types import JSONDict

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
logger.info("bot token: %s", BOT_TOKEN)

bot = Bot(token=BOT_TOKEN)

ADMIN = os.environ["ADMIN"]


r = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
)


def starter():
    whi = bot.get_webhook_info()
    logger.info("active webhook %s", whi.url)

    tunnel = None
    if (tunnel_file := pathlib.Path("wh.json")).exists():
        tunnel = json.loads(pathlib.Path(tunnel_file).read_text())["url"]
        logger.info("webhook/overriden %s", tunnel)

    if wh := os.getenv("WH", tunnel):
        if not wh.endswith("/bot"):
            wh += "/bot"
        if whi.url != wh:
            bot.set_webhook(
                url=wh,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
        me = bot.get_me()
        logger.info("me %s", me.username)

    logger.info("wheel %s", ADMIN)
    bot.send_message(
        ADMIN,
        "bot <b>started</b> - [<code>" + __file__.split("/")[-1] + "</code>]",
        parse_mode=ParseMode.HTML,
    )
    if wh:
        bot.send_message(
            ADMIN,
            f"webhook {wh}",
            parse_mode=ParseMode.HTML,
        )
    bot.send_message(
        ADMIN,
        "menu",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("/ping", callback_data="ping")],
            ]
        ),
    )
    bot.set_my_commands(
        [
            BotCommand("/ping", "ping/pong"),
        ]
    )


def finisher():
    bot.send_message(ADMIN, "we're done")


def health() -> dict[str, Any]:
    return {
        "status": "alive",
        "updated_at": os.getenv("UPDATED_AT", "?"),
        "where": os.getenv("WHERE", "?"),
        "bot_token": BOT_TOKEN[:3] + "..." + BOT_TOKEN[-3:],
        "wh": os.getenv("WH", "?").removeprefix("https://")[-16:],
        "redis": os.getenv("REDIS_HOST", "?"),
    }


def ping(update: Update, args: list[str]) -> None:
    if update.message:
        update.message.reply_html(text="pong")
        if not args:
            bot.send_message(ADMIN, "usage: /ping <host>")
            return
        host = args[0]
        response_time = ping3.ping(host)
        if response_time:
            bot.send_message(
                ADMIN,
                f"{host} is up! response time {response_time:.2f} ms",
            )
        else:
            bot.send_message(ADMIN, f"{host} is down!")
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        bot.send_message(from_user_id, "query/pong")


def file(update: Update, args: list[str]) -> None:
    if not args:
        update.message.reply_text("usage: /file <file_id>")
    file_id = args[0]
    needle = cast(bytes, r.get("files:" + file_id))
    print(needle)
    if not needle:
        update.message.reply_text("file not found")
        return
    file_dict = json.loads(needle)
    file_type = file_dict["type"]
    if file_type == "audio":
        bot.send_audio(ADMIN, file_id)
    elif file_type == "video":
        bot.send_video(ADMIN, file_id)
    elif file_type == "voice":
        bot.send_voice(ADMIN, file_id)
    elif file_type == "document":
        bot.send_document(ADMIN, file_id)
    elif file_type == "photo":
        bot.send_photo(ADMIN, file_id)
    else:
        bot.send_message(ADMIN, f"unknown file type [{file_type}]")


ASSET = pathlib.Path(__file__).parent / "asset"

HTML = (ASSET / "tg.html").read_text().replace("{ADMIN}", ADMIN)


def html(update: Update, args: list[str]) -> None:
    bot.send_message(ADMIN, HTML, parse_mode=ParseMode.HTML)


MARKDOWN = (ASSET / "tg.md").read_text().replace("{ADMIN}", ADMIN)


def markdown(update: Update, args: list[str]) -> None:
    bot.send_message(ADMIN, MARKDOWN, parse_mode=ParseMode.MARKDOWN_V2)


def ls(update: Update, args: list[str]) -> None:
    keys = cast(list[bytes], r.keys("files:*"))
    if not keys:
        update.message.reply_text("no files")
        return
    for key in keys:
        file_id = key.decode("utf-8").split(":")[1]
        file_dict = json.loads(cast(bytes, r.get(key)))
        file_type = file_dict["type"]
        if file_type == "photo":
            text = (
                f"photo {file_dict['file_size']}"
                f" {file_dict['width']}x{file_dict['height']}"
                f"\n{file_id}"
            )
        elif file_type == "audio":
            text = f"audio {file_dict['file_size']}\n{file_id}"
        elif file_type == "video":
            text = f"video {file_dict['file_size']}\n{file_id}"
        elif file_type == "voice":
            text = f"voice {file_dict['file_size']}\n{file_id}"
        elif file_type == "document":
            text = (
                f"document {file_dict['file_size']} "
                f"\n{file_dict['file_name']}\n{file_id}"
            )
        else:
            text = f"unknown\n{file_id}"
        update.message.reply_text(text)


def update(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=bot)
    assert update, "update should be present"
    message = update.message
    if message:
        text = message.text
        if text:
            cmd, *args = text.split()
            print(f'cmd: {cmd}, args: {args}')
            commands: dict[str, Callable] = {
                "/ping": ping,
                "/html": html,
                "/markdown": markdown,
                "file": file,
                "ls": ls,
            }
            action = commands.get(cmd)
            if not action:
                message.reply_text(text + " - ha?")

                reactions = (
                    "👍👎❤🔥🥰👏😁🤔🤯😱🤬😢🎉🤩🤮💩🙏👌🕊🤡🥱🥴😍🐳❤‍🔥🌚🌭💯🤣⚡🍌🏆💔🤨"
                    "😐🍓🍾💋🖕😈😴😭🤓👻👨‍💻👀🎃🙈😇😨🤝✍🤗🫡🎅🎄☃💅🤪🗿🆒💘🙉🦄😘💊🙊😎"
                    "👾🤷‍♂🤷🤷‍♀😡"
                )
                predefined = {
                    "thanks": "👍",
                    "poop": "💩",
                    "sad": "😢",
                }
                emoji = predefined.get(text, random.choice(reactions))
                data: JSONDict = {
                    'chat_id': message.chat.id,
                    'message_id': message.message_id,
                    'reaction': [{"type": "emoji", "emoji": emoji}],
                    'is_big': 'a lot' in text,
                }

                bot._post('setMessageReaction', data)
            else:
                action(update, args)
        audio = message.audio
        if audio:
            print(audio)
            audio_dict = audio.to_dict()
            audio_dict["type"] = "audio"
            audio_dict_str = json.dumps(audio_dict, indent=2)
            message.reply_text("audio " + audio.file_id)
            r.set("files:" + audio.file_id, audio_dict_str)
        video = message.video
        if video:
            print(video)
            video_dict = video.to_dict()
            video_dict["type"] = "video"
            video_dict_str = json.dumps(video_dict, indent=2)
            message.reply_text("video " + video.file_id)
            r.set("files:" + video.file_id, video_dict_str)
        voice = message.voice
        if voice:
            print(voice)
            voice_dict = voice.to_dict()
            voice_dict["type"] = "voice"
            voice_dict_str = json.dumps(voice_dict, indent=2)
            message.reply_text("voice " + voice.file_id)
            r.set("files:" + voice.file_id, voice_dict_str)
        document = message.document
        if document:
            print(document)
            document_dict = document.to_dict()
            document_dict["type"] = "document"
            document_dict_str = json.dumps(document_dict, indent=2)
            message.reply_text("document " + document.file_id)
            r.set("files:" + document.file_id, document_dict_str)
        photo = message.photo
        if photo:
            print(photo)
            photo_dict = photo[-1].to_dict()
            photo_dict["type"] = "photo"
            photo_dict_str = json.dumps(photo_dict, indent=2)
            message.reply_text("photo " + photo[-1].file_id)
            r.set("files:" + photo[-1].file_id, photo_dict_str)

    callback_query = update.callback_query
    if callback_query:
        callback_query.answer()
        data = callback_query.data
        if data == "ping":
            ping(update, [])
