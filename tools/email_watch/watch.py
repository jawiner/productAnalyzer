"""
Email Watch: once a day, searches Gmail for everything on the watch list and sends a
Telegram message when a new matching email arrives. Read-only: nothing in Gmail changes.

    python tools/email_watch/watch.py                # check now
    python tools/email_watch/watch.py --if-due       # skip if today's check already succeeded
    python tools/email_watch/watch.py --dry-run      # search and print; send and change nothing
    python tools/email_watch/watch.py --test         # sign in, send a test message, stop
    python tools/email_watch/watch.py add "Title" --query "<gmail search>" [--since D] [--until D] [--note T]
    python tools/email_watch/watch.py list
    python tools/email_watch/watch.py done <id>

The list is tools/email_watch/watchlist.json and the run state is state.json, both
gitignored (they hold personal details). Gmail: GMAIL_ADDRESS + GMAIL_APP_PASSWORD in the
root .env. See workflows/email_watch.md.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from gmail_inbox import GmailInbox, InboxError, Mail  # noqa: E402
from notify import TelegramError  # noqa: E402
import notify  # noqa: E402

LIST_FILE = HERE / "watchlist.json"
STATE_FILE = HERE / "state.json"
LOG_FILE = ROOT / ".tmp" / "email_watch" / "runner.log"
MAX_PER_ITEM = 5  # emails shown per item in one message; the rest are counted
LOOKBACK_DAYS = 2  # searches start this long before the last good check
SEEN_KEEP = 500


# ---------- files ----------

def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def log(line: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M} {line}\n")
    except OSError:
        pass


# ---------- the list ----------

def slug(title: str, taken: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "item"
    out, n = base, 2
    while out in taken:
        out, n = f"{base}-{n}", n + 1
    return out


def add_item(items: list[dict], title: str, query: str, today: date, since: str | None = None,
             until: str | None = None, note: str | None = None) -> dict:
    for d in (since, until):
        if d:
            date.fromisoformat(d)  # raises on a bad date
    item = {
        "id": slug(title, {i["id"] for i in items}),
        "title": title.strip(),
        "query": query.strip(),
        "since": since or today.isoformat(),
        "until": until,
        "note": note,
        "status": "active",
        "added": today.isoformat(),
    }
    items.append(item)
    return item


def find(items: list[dict], ident: str) -> dict:
    for item in items:
        if item["id"] == ident:
            return item
    raise SystemExit(f"No item with id {ident!r}. See: python tools/email_watch/watch.py list")


# ---------- the check ----------

def search_from(item: dict, state: dict) -> date:
    start = date.fromisoformat(item["since"])
    if state.get("last_ok"):
        start = max(start, date.fromisoformat(state["last_ok"]) - timedelta(days=LOOKBACK_DAYS))
    return start - timedelta(days=1)  # Gmail's after: works in its own time zone: start a day early


def mail_block(m: Mail) -> str:
    e = html.escape
    lines = [f"From: {e(m.sender)}", f"<b>{e(m.subject)}</b>"]
    if m.when:
        lines.append(e(m.when))
    if m.snippet:
        lines.append(e(m.snippet))
    if m.link:
        lines.append(f'<a href="{e(m.link)}">Open in Gmail</a>')
    return "\n".join(lines)


def item_message(item: dict, mails: list[Mail], more: int) -> str:
    total = len(mails) + more
    head = f"📬 <b>{html.escape(item['title'])}</b>: {total} new email{'s' if total != 1 else ''}"
    if item.get("note"):
        head += f"\n<i>{html.escape(item['note'])}</i>"
    blocks = [head] + [mail_block(m) for m in mails]
    if more:
        blocks.append(f"…and {more} more. Search Gmail for: {html.escape(item['query'])}")
    return "\n\n".join(blocks)


def summary(items: list[dict]) -> str:
    active = [i for i in items if i["status"] == "active"]
    if not active:
        return "🗂 <b>Email Watch</b> is running. The watch list is empty."
    lines = [f"🗂 <b>Email Watch</b>: watching {len(active)} thing{'s' if len(active) != 1 else ''}"]
    for i in active:
        until = f", until {i['until']}" if i.get("until") else ""
        lines.append(f"• {html.escape(i['title'])} (since {i['since']}{until})")
    return "\n".join(lines)


def check(items: list[dict], state: dict, open_inbox, send, today: date, dry_run: bool = False, out=print) -> int:
    """0 = checked (and sent anything new), 1 = Gmail problem, 2 = Telegram problem.
    `items` and `state` are changed in place only when the check fully succeeds."""
    expired = [i for i in items if i["status"] == "active" and i.get("until") and today > date.fromisoformat(i["until"])]
    active = [i for i in items if i["status"] == "active" and i not in expired]
    messages, fresh_by_item = [], {}
    try:
        with open_inbox() as inbox:
            for item in active:
                query = f"({item['query']}) after:{search_from(item, state):%Y/%m/%d}"
                hits = inbox.search(query)
                seen = set(state.get("seen", {}).get(item["id"], []))
                fresh = sorted((m for m in hits if m not in seen), key=int)
                if not fresh:
                    continue
                shown = fresh[-MAX_PER_ITEM:]
                mails = [inbox.fetch(hits[m]) for m in shown]
                messages.append(item_message(item, mails, len(fresh) - len(shown)))
                fresh_by_item[item["id"]] = fresh
    except InboxError as exc:
        state["last_error"] = str(exc)
        if dry_run:
            out(f"Gmail problem: {exc}")
            return 1
        if state.get("last_error_alert") != today.isoformat():
            try:
                send(f"⚠️ <b>Email Watch</b> couldn't check Gmail: {html.escape(str(exc))}")
                state["last_error_alert"] = today.isoformat()
            except TelegramError:
                pass
        return 1

    for i in expired:
        messages.append(f"⏹ Stopped watching <b>{html.escape(i['title'])}</b>: its end date ({i['until']}) has passed.")
    weekly = today.weekday() == 6 and state.get("last_summary") != today.isoformat()  # Sundays
    if weekly:
        messages.append(summary([i for i in items if i not in expired]))
    text = "\n\n".join(messages)

    if dry_run:
        out(text or "Nothing new.")
        return 0
    if text:
        try:
            send(text)
        except TelegramError as exc:
            state["last_error"] = str(exc)
            return 2

    for ident, fresh in fresh_by_item.items():
        seen = state.setdefault("seen", {}).setdefault(ident, [])
        seen.extend(fresh)
        del seen[:-SEEN_KEEP]
    for i in expired:
        i["status"] = "expired"
    if weekly:
        state["last_summary"] = today.isoformat()
    state["last_ok"] = today.isoformat()
    state["last_error"] = None
    return 0


# ---------- command line ----------

def gmail_login() -> tuple[str, str]:
    env = dotenv_values(ROOT / ".env")
    address = (env.get("GMAIL_ADDRESS") or "").strip()
    password = (env.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    if not address or not password:
        raise SystemExit("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must both be in the root .env")
    return address, password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Watches Gmail for the things on the list and reports on Telegram.")
    parser.add_argument("--if-due", action="store_true", help="Do nothing if today's check already succeeded")
    parser.add_argument("--dry-run", action="store_true", help="Search and print; send and change nothing")
    parser.add_argument("--test", action="store_true", help="Sign in to Gmail, send a test message, stop")
    sub = parser.add_subparsers(dest="cmd")
    p_add = sub.add_parser("add", help="Watch for something new")
    p_add.add_argument("title")
    p_add.add_argument("--query", required=True, help="Gmail search, e.g. 'from:garmin.com developer'")
    p_add.add_argument("--since", help="YYYY-MM-DD, default today")
    p_add.add_argument("--until", help="YYYY-MM-DD: stop watching after this day")
    p_add.add_argument("--note", help="Shown with each match")
    sub.add_parser("list", help="Show the watch list")
    p_done = sub.add_parser("done", help="Stop watching an item")
    p_done.add_argument("id")
    args = parser.parse_args(argv)

    today = date.today()
    items = load(LIST_FILE, {"items": []})["items"]
    state = load(STATE_FILE, {})

    if args.cmd == "add":
        item = add_item(items, args.title, args.query, today, args.since, args.until, args.note)
        save(LIST_FILE, {"items": items})
        print(f"Watching {item['title']!r} as {item['id']}: {item['query']} (since {item['since']})")
        return 0
    if args.cmd == "list":
        for i in items:
            print(f"[{i['status']}] {i['id']}: {i['title']} | {i['query']} | since {i['since']}"
                  + (f" until {i['until']}" if i.get("until") else ""))
        print(f"Last good check: {state.get('last_ok') or 'never'}" + (f" | last problem: {state['last_error']}" if state.get("last_error") else ""))
        return 0
    if args.cmd == "done":
        find(items, args.id)["status"] = "done"
        save(LIST_FILE, {"items": items})
        print(f"Stopped watching {args.id}.")
        return 0

    if args.if_due and state.get("last_ok") == today.isoformat():
        return 0
    address, password = gmail_login()
    open_inbox = lambda: GmailInbox(address, password)  # noqa: E731

    if args.test:
        with open_inbox() as inbox:
            count = len(inbox.search("newer_than:1d"))
        active = sum(1 for i in items if i["status"] == "active")
        text = (f"✅ <b>Email Watch</b> is connected to {html.escape(address)} ({count} emails in the last day). "
                f"Watching {active} thing{'s' if active != 1 else ''}; it checks once a day.")
        notify.send(text)
        print(f"Signed in to {address}; {count} emails in the last day. Test message sent to Telegram.")
        return 0

    code = check(items, state, open_inbox, notify.send, today, dry_run=args.dry_run)
    if not args.dry_run:
        save(LIST_FILE, {"items": items})
        save(STATE_FILE, state)
        log(f"exit {code} | active {sum(1 for i in items if i['status'] == 'active')}"
            + (f" | {state['last_error']}" if state.get("last_error") else ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
