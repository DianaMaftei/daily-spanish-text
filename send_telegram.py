"""
Sends a Telegram message with a link to today's generated lesson page,
plus the topic if docs/meta.json (written by generate_lesson.py) is
available.

Requires environment variables:
  TELEGRAM_BOT_TOKEN - token from @BotFather
  TELEGRAM_CHAT_ID   - the chat id to send the message to
  GITHUB_REPOSITORY  - "owner/repo", set automatically by GitHub Actions

No external dependencies - standard library only.
"""

import json
import os
import pathlib
import urllib.parse
import urllib.request

META_PATH = pathlib.Path(__file__).parent / "docs" / "meta.json"


def pages_url() -> str:
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    return f"https://{owner}.github.io/{repo}/"


def load_meta() -> dict:
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.load(resp)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    base_url = pages_url()
    meta = load_meta()
    topic = meta.get("topic", "")
    path = meta.get("path", "")  # e.g. "lessons/2026-09-13.html"

    lesson_url = base_url + path if path else base_url

    if topic:
        message = f"Tu lección de español de hoy:\n{topic}\n\n{lesson_url}"
    else:
        message = f"Tu lección de español de hoy está lista:\n{lesson_url}"

    send_telegram(token, chat_id, message)
    print("Sent:", message)


if __name__ == "__main__":
    main()
