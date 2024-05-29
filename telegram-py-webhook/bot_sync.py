import json
import logging
import os
import pathlib
from typing import Any

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


def ping(update: Update) -> None:
    if update.message:
        update.message.reply_html(text="pong")
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        bot.send_message(from_user_id, "query pong")


def update(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=bot)
    assert update, "update should be present"
    message = update.message
    if message:
        text = message.text
        if text:
            if text.startswith("/"):
                cmd = text.split()[0]
                commands = {"/ping": ping}
                action = commands.get(cmd)
                if not action:
                    message.reply_text("ha?")
                else:
                    action(update)
            else:
                message.reply_text(text + " - ha?")
    callback_query = update.callback_query
    if callback_query:
        callback_query.answer()
        data = callback_query.data
        if data == "ping":
            ping(update)
