import os
from typing import Any, cast

import requests

API = "https://api.telegram.org"


class Telegram:
    def __init__(self, token: str) -> None:
        self.token = token

    def file(self, path: str) -> str:
        return f"{API}/file/bot{self.token}/{path}"

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
    ) -> None:
        self._command(
            "answerCallbackQuery",
            {"callback_query_id": callback_query_id, "text": text},
        )

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str | None = None,
    ) -> dict[str, Any]:
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup
        if parse_mode:
            data["parse_mode"] = parse_mode

        response = self._command("sendMessage", data)
        print(response["message_id"])
        return response

    def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
    ) -> dict[str, Any]:
        return self._command(
            "editMessageText",
            {"chat_id": chat_id, "message_id": message_id, "text": text},
        )

    def send_photo(
        self,
        chat_id: int,
        photo: str,
        reply_markup: dict | None = None,
    ) -> None:
        data = {"chat_id": chat_id, "photo": photo}
        if reply_markup:
            data["reply_markup"] = reply_markup
        self._command("sendPhoto", data)

    def send_audio(
        self,
        chat_id: int,
        audio: str,
        reply_markup: dict | None = None,
    ) -> None:
        data = {"chat_id": chat_id, "audio": audio}
        if reply_markup:
            data["reply_markup"] = reply_markup
        self._command("sendAudio", data)

    def send_video(
        self,
        chat_id: int,
        video: str,
        reply_markup: dict | None = None,
    ) -> None:
        data = {"chat_id": chat_id, "video": video}
        if reply_markup:
            data["reply_markup"] = reply_markup
        self._command("sendVideo", data)

    def getFile(self, file_id: str) -> dict:
        return self._command("getFile", {"file_id": file_id})

    def set_webhook(self, url: str, secret_token: str | None = None) -> None:
        secret_token = os.environ.get("TELEGRAM_SECURE_TOKEN", secret_token)
        self._command(
            "setWebhook",
            {
                "url": url,
                "secret_token": secret_token,
                "drop_pending_updates": True,
            },
        )

    def delete_webhook(self) -> None:
        self._command("deleteWebhook")

    def get_webhook_info(self) -> dict[str, str]:
        return self._command("getWebhookInfo")

    def get_me(self) -> dict[str, str]:
        return self._command("getMe")

    def set_my_commands(self, commands: list[dict[str, str]]) -> None:
        self._command("setMyCommands", {"commands": commands})

    def _command(self, cmd: str, data: dict | None = None) -> dict[str, Any]:
        url = f"{API}/bot{self.token}/{cmd}"
        if data:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=data,
            )
        else:
            response = requests.get(url)
        response.raise_for_status()
        result: dict[str, str | dict[str, Any]] = response.json()
        ok = result.get("ok", False)
        if not ok:
            raise Exception("TELEGRAM ERROR", result)
        return cast(dict[str, Any], result["result"])
