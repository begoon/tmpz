import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.responses import Response
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

load_dotenv()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
logger.info("bot token: %s", BOT_TOKEN)

ADMIN = os.environ["ADMIN"]


async def ping(update: Update) -> None:
    if update.message:
        await update.message.reply_html(text="pong")
    if update.callback_query:
        from_user_id = update.callback_query.from_user.id
        await application.bot.send_message(from_user_id, "query pong")


application = Application.builder().token(BOT_TOKEN).updater(None).build()


@asynccontextmanager
async def lifespan(listener: FastAPI):
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
    yield
    await application.bot.send_message(ADMIN, "we're done")


listener = FastAPI(lifespan=lifespan)


@listener.post("/bot")
async def update(request: dict[str, Any]) -> Response:
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
    callback_query = update.callback_query
    if callback_query:
        await callback_query.answer()
        data = callback_query.data
        if data == "ping":
            await ping(update)
    return Response()


@listener.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "alive"}
