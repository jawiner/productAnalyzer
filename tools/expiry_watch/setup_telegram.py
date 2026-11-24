"""
One-time: finds your chat with the bot and sends a test message.

Before running: TELEGRAM_BOT_TOKEN is in .env, and you pressed Start in the bot.

Usage:
    python tools/expiry_watch/setup_telegram.py
"""

import sys

from renewals import NotionError, load_config, save_config
from telegram_send import TelegramError, call, load_token, send


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        cfg = load_config()
        token = load_token()
        bot = call(token, "getMe")
        print(f"Bot: @{bot.get('username')}")

        if (call(token, "getWebhookInfo") or {}).get("url"):
            print("This bot is already wired to another app (it has a webhook), so its messages "
                  "can't be read here. Create a separate bot for the renewal alerts with @BotFather "
                  "and put its token in .env as TELEGRAM_BOT_TOKEN.")
            return 2

        updates = call(token, "getUpdates", {"timeout": 0, "allowed_updates": ["message"]}) or []
        chats = [u["message"]["chat"] for u in updates
                 if u.get("message", {}).get("chat", {}).get("type") == "private"]
        if not chats:
            print(f"No message from you yet. Open @{bot.get('username')} in Telegram, press Start "
                  f"(or send any message), then run this again.")
            return 2

        chat = chats[-1]
        cfg["telegram_chat_id"] = chat["id"]
        save_config(cfg)
        send("✅ <b>Connected</b>\nRenewal alerts will arrive in this chat.", token, str(chat["id"]))
        print(f"Connected to {chat.get('first_name') or 'your'} chat. A test message was sent.")
        return 0
    except (TelegramError, NotionError) as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
