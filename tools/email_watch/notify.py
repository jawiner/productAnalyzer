"""
Sends Email Watch messages through the same Telegram bot as Expiry Watch.

Token: TELEGRAM_BOT_TOKEN in the root .env. Chat: TELEGRAM_CHAT_ID in .env, else the chat
Expiry Watch found (tools/expiry_watch/board.json). The token sits in the request URL, so
request errors are never passed on as they are.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent.parent
EXPIRY_BOARD = ROOT / "tools" / "expiry_watch" / "board.json"
LIMIT = 3900  # Telegram allows 4096 characters per message


class TelegramError(RuntimeError):
    pass


def credentials() -> tuple[str, str]:
    env = dotenv_values(ROOT / ".env")
    token = (env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN isn't in .env (see workflows/expiry_watch.md for the bot setup)")
    chat = (env.get("TELEGRAM_CHAT_ID") or "").strip()
    if not chat and EXPIRY_BOARD.exists():
        try:
            chat = str(json.loads(EXPIRY_BOARD.read_text(encoding="utf-8")).get("telegram_chat_id") or "").strip()
        except (OSError, ValueError):
            chat = ""
    if not chat:
        raise TelegramError("No Telegram chat yet: run python tools/expiry_watch/setup_telegram.py once")
    return token, chat


def pieces(text: str) -> list[str]:
    """Splits a long message between blocks (blank lines), never inside one."""
    out, current = [], ""
    for part in text.split("\n\n"):
        candidate = f"{current}\n\n{part}" if current else part
        if len(candidate) > LIMIT and current:
            out.append(current)
            current = part
        else:
            current = candidate
    return out + ([current] if current else [])


def send(text: str) -> None:
    token, chat = credentials()
    for piece in pieces(text):
        try:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30, json={
                "chat_id": chat, "text": piece[:4096], "parse_mode": "HTML", "disable_web_page_preview": True})
        except requests.RequestException as exc:
            raise TelegramError(f"Can't reach Telegram ({type(exc).__name__})") from None
        try:
            data = r.json()
        except ValueError:
            raise TelegramError(f"Telegram answered {r.status_code} with something unreadable") from None
        if not data.get("ok"):
            raise TelegramError(f"Telegram refused ({r.status_code}): {data.get('description', 'no reason given')}")
