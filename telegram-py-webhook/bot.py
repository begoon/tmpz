import asyncio
import json
import logging
import os
import pathlib
import random
from typing import Any, Callable, cast

import ping3  # type: ignore
import redis
from telegram import (
    Bot,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode

loop = asyncio.new_event_loop()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
logger.info("bot token %s", BOT_TOKEN)

SECRET_TOKEN = os.environ["TELEGRAM_SECRET_TOKEN"]

bot = Bot(token=BOT_TOKEN)

WHEEL = os.environ["WHEEL"]


r = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
)


async def set_webhook() -> str | None:
    whi = await bot.get_webhook_info()
    logger.info("active webhook %s", whi.url)

    tunnel = None
    if (tunnel_file := pathlib.Path("wh.json")).exists():
        tunnel = json.loads(pathlib.Path(tunnel_file).read_text())["url"]
        logger.info("webhook/override %s", tunnel)

    if wh := os.getenv("WH", tunnel):
        if not wh.endswith("/bot"):
            wh += "/bot"
        if whi.url != wh:
            await bot.set_webhook(
                url=wh,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                secret_token=SECRET_TOKEN,
            )
    return wh


def starter():
    loop.run_until_complete(starter_async())


async def starter_async():
    if False:
        wh = await set_webhook()
        await bot.send_message(WHEEL, f"webhook {wh}")

    me = await bot.get_me()
    logger.info("me %s", me.username)

    logger.info("wheel %s", WHEEL)
    await bot.send_message(
        WHEEL,
        "bot <b>started</b>",
        parse_mode=ParseMode.HTML,
    )

    await bot.send_message(
        WHEEL,
        "menu",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("/ping", callback_data="/ping"),
                    InlineKeyboardButton("/me", callback_data="/me"),
                ],
                [
                    InlineKeyboardButton("/html", callback_data="/html"),
                    InlineKeyboardButton(
                        "/markdown", callback_data="/markdown"
                    ),
                ],
                [
                    InlineKeyboardButton("/ls", callback_data="/ls"),
                ],
                [InlineKeyboardButton("what?", callback_data="what?")],
            ]
        ),
    )
    await set_commands()


def reduct(text: str, sz: int = 8) -> str:
    return text[:sz] + "..." + text[-sz:]


def health() -> dict[str, Any]:
    return loop.run_until_complete(health_async())


async def health_async() -> dict[str, Any]:
    wh = (await bot.get_webhook_info()).url
    return {
        "status": "alive",
        "updated_at": os.getenv("UPDATED_AT", "?"),
        "where": os.getenv("WHERE", "?"),
        "bot_token": reduct(os.getenv("BOT_TOKEN", "?")),
        "webhook": wh.removeprefix("https://"),
        "redis": reduct(os.getenv("REDIS_HOST", "?"), 8),
    }


async def ping(update: Update, args: list[str]) -> None:
    """ping"""
    if update.message:
        await update.message.reply_html(text="ping")
        if not args:
            await bot.send_message(WHEEL, "usage: /ping <host>")
            return
        host = args[0]
        response_time = ping3.ping(host)
        if response_time:
            await bot.send_message(
                WHEEL,
                f"{host} is up! response time {response_time:.2f} ms",
            )
        else:
            await bot.send_message(WHEEL, f"{host} is down!")
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        await bot.send_message(from_user_id, "query/ping")


async def file(update: Update, args: list[str]) -> None:
    """file info"""
    if not args and update.message:
        await update.message.reply_text("usage: /file <file_id>")
    file_id = args[0]
    needle = cast(bytes, r.get("files:" + file_id))
    logger.info(needle)
    if not needle and update.message:
        await update.message.reply_text("file not found")
        return
    file_dict = json.loads(needle)
    file_type = file_dict["type"]
    if file_type == "audio":
        await bot.send_audio(WHEEL, file_id)
    elif file_type == "video":
        await bot.send_video(WHEEL, file_id)
    elif file_type == "voice":
        await bot.send_voice(WHEEL, file_id)
    elif file_type == "document":
        await bot.send_document(WHEEL, file_id)
    elif file_type == "photo":
        await bot.send_photo(WHEEL, file_id)
    else:
        await bot.send_message(WHEEL, f"unknown file type [{file_type}]")


ASSET = pathlib.Path(__file__).parent / "asset"

HTML = (ASSET / "tg.html").read_text().replace("{WHEEL}", WHEEL)


async def html(update: Update, args: list[str]) -> None:
    """html message"""
    await bot.send_message(WHEEL, HTML, parse_mode=ParseMode.HTML)


MARKDOWN = (ASSET / "tg.md").read_text().replace("{WHEEL}", WHEEL)


async def markdown(update: Update, args: list[str]) -> None:
    """markdown message"""
    await bot.send_message(WHEEL, MARKDOWN, parse_mode=ParseMode.MARKDOWN_V2)


async def ls(update: Update, args: list[str]) -> None:
    """list files"""
    keys = cast(list[bytes], r.keys("files:*"))
    if not keys and update.message:
        await update.message.reply_text("no files")
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
        if update.message:
            await update.message.reply_text(text)
        if update.callback_query:
            from_user_id = update.callback_query.from_user.id
            await bot.send_message(from_user_id, text)


async def me(update: Update, args: list[str]) -> None:
    """me"""
    info = health()
    content = json.dumps(info, indent=2)
    if update.message:
        await update.message.reply_text(content)
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        await bot.send_message(from_user_id, content)


COMMANDS: dict[str, Callable] = {
    "/ping": ping,
    "/html": html,
    "/markdown": markdown,
    "/file": file,
    "/ls": ls,
    "/me": me,
}


async def set_commands() -> None:
    commands = [
        BotCommand(cmd, handler.__doc__ or "")
        for cmd, handler in COMMANDS.items()
    ]
    for cmd in commands:
        logger.info(f'{cmd.command} {cmd.description=}')
    await bot.set_my_commands(commands)


def update(request):
    loop.run_until_complete(update_async(request))


async def update_async(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=bot)
    assert update, "update should be present"

    effective_user = update.effective_user
    if effective_user and effective_user.id != int(WHEEL):
        await bot.send_message(WHEEL, "are you talking to me?")
        return

    message = update.message
    if message:
        text = message.text
        if text:
            cmd, *args = text.split()
            logger.info(f'{cmd=} {args=}')
            action = COMMANDS.get(cmd)
            if not action:
                await message.reply_text(text + " - ha?")

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
                await bot.set_message_reaction(
                    message.chat.id,
                    message.message_id,
                    ("emoji", emoji),
                )
            else:
                action(update, args)
        audio = message.audio
        if audio:
            print(audio)
            audio_dict = audio.to_dict()
            audio_dict["type"] = "audio"
            audio_dict_str = json.dumps(audio_dict, indent=2)
            await message.reply_text("audio " + audio.file_id)
            r.set("files:" + audio.file_id, audio_dict_str)
        video = message.video
        if video:
            print(video)
            video_dict = video.to_dict()
            video_dict["type"] = "video"
            video_dict_str = json.dumps(video_dict, indent=2)
            await message.reply_text("video " + video.file_id)
            r.set("files:" + video.file_id, video_dict_str)
        voice = message.voice
        if voice:
            print(voice)
            voice_dict = voice.to_dict()
            voice_dict["type"] = "voice"
            voice_dict_str = json.dumps(voice_dict, indent=2)
            await message.reply_text("voice " + voice.file_id)
            r.set("files:" + voice.file_id, voice_dict_str)
        document = message.document
        if document:
            print(document)
            document_dict = document.to_dict()
            document_dict["type"] = "document"
            document_dict_str = json.dumps(document_dict, indent=2)
            await message.reply_text("document " + document.file_id)
            r.set("files:" + document.file_id, document_dict_str)
        photo = message.photo
        if photo:
            print(photo)
            photo_dict = photo[-1].to_dict()
            photo_dict["type"] = "photo"
            photo_dict_str = json.dumps(photo_dict, indent=2)
            await message.reply_text("photo " + photo[-1].file_id)
            r.set("files:" + photo[-1].file_id, photo_dict_str)

    callback_query = update.callback_query
    if callback_query:
        await callback_query.answer()
        query_data = callback_query.data
        if query_data:
            cmd, *args = query_data.split()
            logger.info(f'{cmd=} {args=}')
            action = COMMANDS.get(cmd)
            if action:
                await action(update, args)
            else:
                await bot.send_message(WHEEL, query_data + " - query/ha?")
