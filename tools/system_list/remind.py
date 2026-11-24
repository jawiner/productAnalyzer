"""
System list reminders: one Telegram message a day at most, from the same bot as the
renewal check.

  - Every Sunday (or the first run of a new week): a summary of the whole list:
    urgent items, what comes due in the next 4 weeks, what's overdue, what only the
    owner can do, and how many open items each system has.
  - Any day: a reminder for each open row whose "Remind on" date has come, and for each
    row with a Due date 7 days before it and again the day before.

Usage:
    python tools/system_list/remind.py              # the daily run
    python tools/system_list/remind.py --dry-run    # show the message, send and change nothing
    python tools/system_list/remind.py --if-due     # skip if today's run already succeeded
    python tools/system_list/remind.py --summary    # send the weekly summary now
    python tools/system_list/remind.py --test-message
"""

import argparse
import html
import json
import re
import sys
import traceback
from collections import Counter
from datetime import date, datetime, timedelta

# todo_table first: it puts the expiry watch's folder (telegram_send) on the import path.
from todo_table import (P_PINGED, STATE_DIR, Item, Notion, NotionError, date_prop, load_config,
                        read_all, telegram_config)
import telegram_send  # noqa: E402

STATE_PATH = STATE_DIR / "state.json"
LOG_PATH = STATE_DIR / "runner.log"
DUE_LEADS = (1, 7)          # days before a Due date that a reminder goes out
COMING_DAYS = 28            # the summary's "coming due" window
SECTION_MAX = 8             # rows per summary section before "+N more"
MORNING_HOUR = 8            # scheduled runs (--if-due) send nothing before 08:00


def log(message: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}"
    if sys.stdout:  # pythonw has none
        print(message)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def week_id(today: date) -> str:
    """Weeks start on Sunday here."""
    year, week, _ = (today + timedelta(days=1)).isocalendar()
    return f"{year}-W{week:02d}"


def nice(d: date) -> str:
    return f"{d:%a} {d.day} {d:%b}"


def ping_reason(it: Item, today: date) -> str | None:
    """Why this row should be reminded about today, or None."""
    if not it.open:
        return None
    last = it.pinged
    if it.remind and it.remind <= today and (last is None or last < it.remind):
        return "remind"
    if it.due:
        days = (it.due - today).days
        for lead in DUE_LEADS:  # the closest stage first
            if days <= lead and (last is None or last < it.due - timedelta(days=lead)):
                return "overdue" if days < 0 else "due"
    return None


def esc(text: str) -> str:
    """Escapes for Telegram's HTML mode; quotes stay readable (they only matter inside attributes)."""
    return html.escape(text, quote=False)


def _line(it: Item, today: date, *, with_why: bool = False) -> str:
    text = f"• <b>{esc(it.system or 'Other')}</b>: {esc(it.item)}"
    extra = []
    if it.due:
        days = (it.due - today).days
        extra.append(f"overdue since {nice(it.due)}" if days < 0 else
                     "due today" if days == 0 else f"due {nice(it.due)}")
    if with_why and it.why:
        extra.append(esc(it.why))
    return text + (f"\n   <i>{' · '.join(extra)}</i>" if extra else "")


def _section(title: str, rows: list[Item], today: date, **kw) -> list[str]:
    if not rows:
        return []
    lines = ["", title]
    lines += [_line(it, today, **kw) for it in rows[:SECTION_MAX]]
    if len(rows) > SECTION_MAX:
        lines.append(f"   …and {len(rows) - SECTION_MAX} more in the list")
    return lines


def by_urgency(rows: list[Item]) -> list[Item]:
    return sorted(rows, key=lambda it: (it.rank, it.due or date.max, it.system, it.item))


def format_pings(rows: list[Item], today: date, link: str) -> str:
    lines = ["⏰ <b>Reminders for today</b>", ""]
    lines += [_line(it, today, with_why=True) for it in by_urgency(rows)]
    lines += ["", "Done? Set its Status to Done. Not yet? Move “Remind on” to a later day."]
    if link:
        lines.append(f'<a href="{html.escape(link)}">Open the System list</a>')
    return "\n".join(lines)


def format_summary(items: list[Item], today: date, link: str, pings: list[Item]) -> str:
    open_rows = [it for it in items if it.open]
    systems = Counter(it.system or "Other" for it in open_rows)
    yours = [it for it in open_rows if it.who == "You"]
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)  # Sunday
    lines = [f"🗂 <b>System list</b> · week of {nice(week_start)}",
             f"{len(open_rows)} open item{'s' if len(open_rows) != 1 else ''} across "
             f"{len(systems)} system{'s' if len(systems) != 1 else ''} · {len(yours)} only you can do"]
    if not open_rows:
        lines.append("Nothing open. 🎉")
    overdue = by_urgency([it for it in open_rows if it.due and it.due < today])
    coming = sorted((it for it in open_rows if it.due and 0 <= (it.due - today).days <= COMING_DAYS),
                    key=lambda it: (it.due, it.rank))
    shown = {id(it) for it in overdue + coming}
    urgent = by_urgency([it for it in open_rows if it.priority == "P0" and id(it) not in shown])
    shown |= {id(it) for it in urgent}
    today_rows = [it for it in by_urgency(pings) if id(it) not in shown]
    shown |= {id(it) for it in today_rows}
    your_next = by_urgency([it for it in yours if it.priority == "P1" and it.status != "Waiting"
                            and id(it) not in shown])
    lines += _section("⚠️ <b>Overdue</b>", overdue, today)
    lines += _section("🔴 <b>Urgent</b>", urgent, today)
    lines += _section("📅 <b>Coming due (next 4 weeks)</b>", coming, today)
    lines += _section("⏰ <b>Reminders for today</b>", today_rows, today, with_why=True)
    lines += _section("👤 <b>Next steps only you can do</b>", your_next, today)
    if systems:
        lines += ["", "📊 " + " · ".join(f"{esc(name)} {n}" for name, n in systems.most_common())]
    lines += ["", "Mark things Done in the list. Put a date in “Remind on” to get a ping that day."]
    if link:
        lines.append(f'<a href="{html.escape(link)}">Open the System list</a>')
    return "\n".join(lines)


def run(notion, cfg: dict, state: dict, today: date, *, send, dry_run: bool = False,
        force_summary: bool = False, say=log) -> dict:
    """One pass. Notion and Telegram are passed in, so the offline test runs this exact code."""
    items = read_all(notion, cfg["database_id"])
    pings = [it for it in items if ping_reason(it, today)]
    link = cfg.get("page_url") or cfg.get("database_url") or ""
    summary_due = force_summary or state.get("summary_week") != week_id(today)

    if summary_due:
        text = format_summary(items, today, link, pings)
    elif pings:
        text = format_pings(pings, today, link)
    else:
        text = ""

    if text:
        if dry_run:
            say("[dry run] would send to Telegram:\n" + text)
        elif send is None:
            raise telegram_send.TelegramError("Telegram isn't set up, so nothing was sent.")
        else:
            send(text)
            # Only after a good send: if it failed, the next run tries again.
            for it in pings:
                if it.page_id:
                    notion.update_page(it.page_id, {P_PINGED: date_prop(today)})
            if summary_due:
                state["summary_week"] = week_id(today)
    return {"items": len(items), "open": sum(it.open for it in items), "pings": len(pings),
            "summary": summary_due, "sent": bool(text) and not dry_run}


# --- command line -------------------------------------------------------------

def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def safe(text: str) -> str:
    """Error text for the log or a message: first line, with anything token-shaped removed."""
    first = (str(text).strip().splitlines() or [""])[0][:300]
    return re.sub(r"bot\d+:[\w-]+|[A-Za-z0-9_\-]{32,}", "[hidden]", first)


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram reminders for the System list in Notion.")
    parser.add_argument("--dry-run", action="store_true", help="Show the message; send and change nothing")
    parser.add_argument("--if-due", action="store_true", help="Do nothing if today's run already succeeded")
    parser.add_argument("--summary", action="store_true", help="Send the weekly summary now")
    parser.add_argument("--test-message", action="store_true", help="Send a test message and stop")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    today = date.today()
    state = load_state()
    if args.if_due and state.get("last_ok") == today.isoformat():
        return 0
    # The every-3-hours trigger also fires at night; a day's first message waits for the morning.
    if args.if_due and datetime.now().hour < MORNING_HOUR:
        return 0

    try:
        cfg = load_config()
    except NotionError as exc:
        log(str(exc))
        return 2

    sender = None
    try:
        token, chat_id = telegram_send.credentials(telegram_config())
        sender = lambda text: telegram_send.send(text, token, chat_id)  # noqa: E731
    except telegram_send.TelegramError as exc:
        log(str(exc))
        if not args.dry_run:
            return 2

    if args.test_message:
        sender("✅ <b>Test from the System list</b>\nReminders about your systems will arrive here.")
        log("Test message sent.")
        return 0

    try:
        result = run(Notion(), cfg, state, today, send=sender, dry_run=args.dry_run,
                     force_summary=args.summary)
    except Exception as exc:  # noqa: BLE001 - under pythonw a crash would otherwise vanish
        frames = "".join(traceback.format_tb(exc.__traceback__)[-3:])
        log(f"Run failed: {type(exc).__name__}: {safe(exc)}\n{frames}")
        last_ok = state.get("last_ok")
        stale = not last_ok or (today - date.fromisoformat(last_ok)).days >= 2
        if sender and stale and not args.dry_run and state.get("fail_notice") != today.isoformat():
            try:
                sender(f"⚠️ <b>The System list reminder couldn't run</b>\n{html.escape(safe(exc))}\n"
                       f"Last good run: {last_ok or 'never'}.")
                state["fail_notice"] = today.isoformat()
                save_state(state)
            except telegram_send.TelegramError:
                pass
        return 1

    log(f"{result['open']} open of {result['items']} row(s); {result['pings']} reminder(s)"
        + ("; weekly summary" if result["summary"] else "")
        + (" sent" if result["sent"] else " (nothing sent)"))
    if args.dry_run:
        return 0
    state["last_ok"] = today.isoformat()
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
