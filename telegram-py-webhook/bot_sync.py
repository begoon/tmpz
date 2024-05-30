import json
import logging
import os
import pathlib
import random
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


HTML = f"""<b>bold</b>, <strong>bold</strong>
<i>italic</i>, <em>italic</em>
<u>underline</u>, <ins>underline</ins>
<s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
<span class="tg-spoiler">spoiler</span>, <tg-spoiler>spoiler</tg-spoiler>
<b>bold <i>italic bold <s>italic bold strikethrough <span class="tg-spoiler">italic bold strikethrough spoiler</span></s> <u>underline italic bold</u></i> bold</b>
<a href="http://www.example.com/">inline URL</a>
<a href="tg://user?id={ADMIN}">inline mention of a user</a>
<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>
<code>inline fixed-width code</code>
<pre>pre-formatted fixed-width code block</pre>
<pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
<blockquote>Block quotation started\nBlock quotation continued\nThe last line of the block quotation</blockquote>
<blockquote expandable>Expandable block quotation started\nExpandable block quotation continued\nExpandable block quotation continued\nHidden by default part of the block quotation started\nExpandable block quotation continued\nThe last line of the block quotation</blockquote>
"""


def html(update: Update, args: list[str]) -> None:
    bot.send_message(ADMIN, HTML, parse_mode=ParseMode.HTML)


MARKDOWN = f"""*bold \*text*
_italic \*text_
__underline__
~strikethrough~
||spoiler||
*bold _italic bold ~italic bold strikethrough ||italic bold strikethrough spoiler||~ __underline italic bold___ bold*
[inline URL](http://www.example.com/)
[inline mention of a user](tg://user?id=123456789)
![👍](tg://emoji?id=5368324170671202286)
`inline fixed-width code`
```
pre-formatted fixed-width code block
```
```python
pre-formatted fixed-width code block written in the Python programming language
```
>Block quotation started
>Block quotation continued
>Block quotation continued
>Block quotation continued
>The last line of the block quotation
**>The expandable block quotation started right after the previous block quotation
>It is separated from the previous block quotation by an empty bold entity
>Expandable block quotation continued
>Hidden by default part of the expandable block quotation started
>Expandable block quotation continued
>The last line of the expandable block quotation with the expandability mark||
"""


def markdown(update: Update, args: list[str]) -> None:
    bot.send_message(ADMIN, MARKDOWN, parse_mode=ParseMode.MARKDOWN_V2)


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
                "/file": file,
                "/html": html,
                "/markdown": markdown,
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
