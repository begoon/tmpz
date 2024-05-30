import json
import logging
import os
import pathlib
from typing import Any, Callable

import ping3
from telegram import (
    Bot,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
logger.info("bot token: %s", BOT_TOKEN)

bot = Bot(token=BOT_TOKEN)

ADMIN = os.environ["ADMIN"]


def starter():
    wh_default = None
    wh_file = pathlib.Path("wh.json")
    if wh_file.exists():
        with wh_file.open() as f:
            wh_default = json.load(f)["url"]  # noqa: F821
            logger.info("webhook/wh.json %s", wh_default)

    if wh := os.getenv("WH", wh_default):
        if not wh.endswith("/bot"):
            wh += "/bot"
        whi = bot.get_webhook_info()
        logger.info("webhook %s", whi.url)
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
    bot.send_document(ADMIN, file_id)


def update(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=bot)
    assert update, "update should be present"
    message = update.message
    if message:
        text = message.text
        if text:
            if text.startswith("/"):
                cmd, *args = text.split()
                print(f'cmd: {cmd}, args: {args}')
                commands: dict[str, Callable] = {"/ping": ping, "/file": file}
                action = commands.get(cmd)
                if not action:
                    message.reply_text("ha?")
                else:
                    action(update, args)
            else:
                message.reply_text(text + " - ha?")
        audio = message.audio
        if audio:
            print(audio, json.dumps(audio.to_dict(), indent=2))
            message.reply_text("audio " + audio.file_id)
        video = message.video
        if video:
            print(video, json.dumps(video.to_dict(), indent=2))
            message.reply_text("video " + video.file_id)
        voice = message.voice
        if voice:
            print(voice, json.dumps(voice.to_dict(), indent=2))
            message.reply_text("voice " + voice.file_id)
        document = message.document
        if document:
            print(document, json.dumps(document.to_dict(), indent=2))
            message.reply_text("document " + document.file_id)
        photo = message.photo
        if photo:
            print(photo, json.dumps(photo[-1].to_dict(), indent=2))
            message.reply_text("photo " + photo[-1].file_id)

    callback_query = update.callback_query
    if callback_query:
        callback_query.answer()
        data = callback_query.data
        if data == "ping":
            ping(update, [])
