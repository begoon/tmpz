import json
import logging
import os
import time
import traceback
from typing import Any, Callable

import telegram.vendor.ptb_urllib3.urllib3 as urllib3
from telegram import (
    Bot,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)

from application import settings

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


def starter():
    me = bot.get_me()
    logger.info("me %s", me.username)

    logger.info("wheel %s", WHEEL)
    bot.send_message(WHEEL, "bot <b>started</b>", parse_mode=ParseMode.HTML)

    bot.send_message(
        WHEEL,
        "menu",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("/ping", callback_data="/ping"),
                    InlineKeyboardButton("/me", callback_data="/me"),
                    InlineKeyboardButton("/you", callback_data="/you"),
                ],
                [InlineKeyboardButton("what?", callback_data="what?")],
            ]
        ),
    )
    set_commands()


def health() -> dict[str, Any]:
    return {
        "status": "alive",
        "version": settings.VERSION,
        "updated_at": os.getenv("UPDATED_AT", "?"),
        "tag": os.getenv("TAG", "?"),
        "where": os.getenv("WHERE", "?"),
    }


def ping_(host: str) -> int:
    if not host.startswith("http"):
        host = "https://" + host
    response = urllib3.PoolManager().request("GET", host, timeout=1, retries=0)
    return response.status


def ping(update: Update, args: list[str]) -> None:
    """ping"""
    if update.message:
        if not args:
            bot.send_message(WHEEL, "usage: /ping <host>")
            return
        sent = update.message.reply_html(text="pinging " + args[0] + "...")
        try:
            started = time.time()
            status = ping_(args[0])
            elapsed = time.time() - started
            bot.edit_message_text(
                chat_id=sent.chat_id,
                message_id=sent.message_id,
                text=f"{args[0]} responded with {status} in {elapsed:.2f}s",
            )
        except Exception as e:
            update.message.reply_text(str(e))
            print(traceback.format_exc())

    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        bot.send_message(from_user_id, "query/ping")


def me(update: Update, args: list[str]) -> None:
    """me"""
    info = health()
    content = json.dumps(info, indent=2)
    if update.message:
        update.message.reply_text(content)
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        bot.send_message(from_user_id, content)


def you(update: Update, args: list[str]) -> None:
    """you"""
    content = json.dumps(update.to_dict(), indent=2)
    if update.message:
        update.message.reply_text(content, parse_mode=ParseMode.HTML)
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        bot.send_message(from_user_id, content, parse_mode=ParseMode.HTML)


COMMANDS: dict[str, Callable] = {
    "/ping": ping,
    "/me": me,
    "/you": you,
}


def set_commands() -> None:
    commands = [
        BotCommand(cmd, handler.__doc__ or "")
        for cmd, handler in COMMANDS.items()
    ]
    for cmd in commands:
        logger.info(f'{cmd.command} {cmd.description=}')
    bot.set_my_commands(commands)


def update(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=bot)
    assert update, "update should be present"

    effective_user = update.effective_user
    if effective_user and effective_user.id != int(WHEEL):
        bot.send_message(WHEEL, "are you talking to me?")
        return

    message = update.message
    if message:
        text = message.text
        if text:
            cmd, *args = text.split()
            logger.info(f'{cmd=} {args=}')
            action = COMMANDS.get(cmd)
            if not action:
                message.reply_text(text + " - ha?")
            else:
                action(update, args)

    callback_query = update.callback_query
    if callback_query:
        callback_query.answer()
        query_data = callback_query.data
        cmd, *args = query_data.split()
        logger.info(f'{cmd=} {args=}')
        action = COMMANDS.get(cmd)
        if action:
            action(update, args)
        else:
            bot.send_message(WHEEL, query_data + " - query/ha?")
