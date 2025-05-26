import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
APPLICATION_URL = os.environ["APPLICATION_URL"]
print(APPLICATION_URL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/start webapp":
        keyboard = [
            [
                KeyboardButton(
                    text="Open Mini App",
                    web_app=WebAppInfo(url=APPLICATION_URL),
                )
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Click the button below to open the Web App:",
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            "Aloha! Type /start webapp to open the Mini App."
        )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ha? " + update.message.text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Open Mini App",
                        web_app=WebAppInfo(url=APPLICATION_URL),
                    )
                ]
            ]
        ),
    )


async def web_app_data_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    data = update.message.web_app_data.data
    await update.message.reply_text(f"received web app data: {data}")


app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
app.add_handler(
    MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler)
)

app.run_polling()
