import json
import os
from typing import Any, Callable

from telegram_ import Telegram

BOT_TOKEN = os.environ["BOT_TOKEN"]
print("bot token", BOT_TOKEN)

bot = Telegram(BOT_TOKEN)

WHEEL = int(os.environ["WHEEL"])


def starter():
    me = bot.get_me()
    print("me", me["username"])

    print("wheel", WHEEL)
    bot.send_message(WHEEL, "bot <b>started</b>", parse_mode="HTML")
    bot.send_message(
        WHEEL,
        "menu",
        parse_mode="HTML",
        reply_markup={
            "inline_keyboard": [
                [{"text": "callback", "callback_data": "ping"}]
            ],
        },
    )
    set_commands()


def echo(user_id: int, update: dict[str, Any]) -> None:
    message = update["message"]
    bot.send_message(user_id, f'asking "{message["text"]}"?')


def edit(user_id: int, update: dict[str, Any]) -> None:
    message = update["message"]
    _, *args = message["text"].split()
    if not args:
        bot.send_message(user_id, "edit what?")
        return
    message_id = int(args[0])
    updated = f'EDITED "{message_id}"' if len(args) == 1 else args[1]
    bot.edit_message_text(user_id, message_id, updated)


def me(user_id: int, update: dict[str, Any]) -> None:
    info = {
        "WHERE": os.getenv("WHERE", "?"),
        "UPDATED_AT": os.getenv("UPDATED_AT", "?"),
    }
    bot.send_message(user_id, json.dumps(info, indent=2))
    me_ = bot.get_me()
    bot.send_message(user_id, json.dumps(me_, indent=2))


def you(user_id: int, update: dict[str, Any]) -> None:
    bot.send_message(user_id, json.dumps(update, indent=2))


COMMANDS: dict[str, Callable] = {
    "/echo": echo,
    "/me": me,
    "/you": you,
    "/edit": edit,
}


def set_commands() -> None:
    commands = [{'command': cmd, 'description': cmd} for cmd in COMMANDS.keys()]
    bot.set_my_commands(commands)


def effective_user(update: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    user = None
    if message := update.get("message"):
        user = message["from"]
    if edited_message := update.get("edited_message"):
        user = edited_message["from"]
    if callback_query := update.get("callback_query"):
        user = callback_query["from"]
    if not user:
        raise ValueError("no user")
    id = user["id"]
    return id, user


def update_(update: dict[str, Any]) -> None:
    assert update, "update should be present"

    user_id, user = effective_user(update)

    if user_id != int(WHEEL):
        bot.send_message(user_id, "are you talking to me?")
        return

    if message := update.get("message"):
        print(f'{message=}')

        if photo := message.get("photo"):
            print(f'{photo=}')
            bot.send_message(user_id, json.dumps(photo, indent=2))
            return

        if document := message.get("document"):
            print(f'{document=}')
            bot.send_message(user_id, json.dumps(document, indent=2))
            return

        if text := message.get("text"):
            cmd = text.split(maxsplit=1)[0]
            print(f'{cmd=} {text=}')
            action = COMMANDS.get(cmd)
            if not action:
                bot.send_message(user_id, f'{text} - ha?')
            else:
                action(user_id, update)

    if callback_query := update.get("callback_query"):
        bot.answer_callback_query(callback_query["id"])
        query_data = callback_query["data"]
        print(f'callback {query_data=}')
        bot.send_message(user_id, f'callback {query_data=}')
