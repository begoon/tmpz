import logging
import os
from typing import Any

from telegram.constants import ParseMode

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
logger.info("bot token: %s", BOT_TOKEN)

application = Application.builder().token(BOT_TOKEN).build()

ADMIN = os.environ["ADMIN"]


async def starter():
    logger.info("wheel %s", ADMIN)
    await application.bot.send_message(
        ADMIN,
        "bot <b>started</b>",
        parse_mode=ParseMode.HTML,
    )
    await application.bot.send_message(
        ADMIN,
        "menu",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("/ping", callback_data="ping")],
            ]
        ),
    )


async def finisher():
    await application.bot.send_message(ADMIN, "we're done")


def health() -> dict[str, Any]:
    return {"status": "alive", "updated_at": os.getenv("UPDATED_AT", "?")}


async def ping(update: Update) -> None:
    if update.message:
        await update.message.reply_html(text="pong")
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        await application.bot.send_message(from_user_id, "query pong")


async def update(request: dict[str, Any]) -> None:
    update = Update.de_json(data=request, bot=application.bot)
    assert update, "update should be present"
    print(update)
    message = update.message
    if message:
        text = message.text
        if text:
            if text.startswith("/"):
                cmd = text.split()[0]
                commands = {"/ping": ping}
                action = commands.get(cmd)
                if not action:
                    await message.reply_text("ha?")
                else:
                    await action(update)
            else:
                await message.reply_text(text + " - ha?")
    callback_query = update.callback_query
    if callback_query:
        await callback_query.answer()
        data = callback_query.data
        if data == "ping":
            await ping(update)
