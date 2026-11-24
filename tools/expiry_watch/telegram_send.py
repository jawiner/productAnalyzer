"""
Sends the alerts to Telegram.

The bot token sits in the request URL, so request errors are never passed on
as they are: only the error's class name or Telegram's own description.
"""

import os
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent.parent
LIMIT = 3900  # Telegram allows 4096 characters per message

SETUP_HELP = (
    "Telegram isn't set up yet.\n"
    "1. In Telegram, open @BotFather, send /newbot and follow the two questions.\n"
    "2. Put the token it gives you in .env as TELEGRAM_BOT_TOKEN=...\n"
    "3. Open your new bot in Telegram and press Start.\n"
    "4. Run: python tools/expiry_watch/setup_telegram.py"
)


class TelegramError(RuntimeError):
    pass


def load_token() -> str:
    token = dotenv_values(ROOT / ".env").get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramError(SETUP_HELP)
    return token.strip()


def credentials(cfg: dict) -> tuple[str, str]:
    token = load_token()
    chat_id = dotenv_values(ROOT / ".env").get("TELEGRAM_CHAT_ID") or cfg.get("telegram_chat_id")
    if not chat_id:
        raise TelegramError("The bot doesn't know where to write yet. Open the bot in Telegram, press "
                            "Start, then run: python tools/expiry_watch/setup_telegram.py")
    return token, str(chat_id).strip()


def call(token: str, method: str, payload: dict | None = None) -> dict:
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=payload or {}, timeout=30)
    except requests.RequestException as exc:
        raise TelegramError(f"Can't reach Telegram ({type(exc).__name__})") from None
    try:
        data = r.json()
    except ValueError:
        raise TelegramError(f"Telegram answered {r.status_code} with something unreadable") from None
    if not data.get("ok"):
        raise TelegramError(f"Telegram refused ({r.status_code}): {data.get('description', 'no reason given')}")
    return data.get("result")


def _pieces(text: str) -> list[str]:
    """Splits a long message between items (blank lines), never inside one."""
    pieces, current = [], ""
    for part in text.split("\n\n"):
        candidate = f"{current}\n\n{part}" if current else part
        if len(candidate) > LIMIT and current:
            pieces.append(current)
            current = part
        else:
            current = candidate
    return pieces + ([current] if current else [])


def send(text: str, token: str, chat_id: str) -> None:
    for piece in _pieces(text):
        call(token, "sendMessage", {"chat_id": chat_id, "text": piece[:4096], "parse_mode": "HTML",
                                    "disable_web_page_preview": True})
