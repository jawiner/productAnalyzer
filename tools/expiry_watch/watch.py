"""
Expiry watcher: one daily pass over everything that has an end date.

  1. Reads the Renewals table in Notion (my own list).
  2. Looks up the real expiry date of every Domain row and its site certificate.
  3. Tests the API keys in .env with free calls (values never shown).
  4. Sends one Telegram message with whatever reached a warning day or broke.

Usage:
    python tools/expiry_watch/watch.py              # the daily run
    python tools/expiry_watch/watch.py --dry-run    # show what it would do, change nothing
    python tools/expiry_watch/watch.py --if-due     # skip if today's run already succeeded
    python tools/expiry_watch/watch.py --test-message
    python tools/expiry_watch/watch.py --heartbeat  # send the weekly "still running" note now
"""

import argparse
import json
import re
import sys
import traceback
from datetime import date, datetime, timedelta

import checks as checks_mod
import rules
import telegram_send
from renewals import (P_ALERTED, P_EXPIRES, P_STATUS, STATE_DIR, Item, Notion, NotionError,
                      date_prop, load_config, new_row, parse_item, text_prop)

STATE_PATH = STATE_DIR / "state.json"
LOG_PATH = STATE_DIR / "runner.log"
ORPHAN_STATUS = "⚪ No longer found, so it isn't checked. Delete the row if it's gone for good"
NOT_A_HOST = "The name isn't a web address, so nothing is looked up"


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


def run(notion, cfg: dict, today: date, *, send, domain_lookup, ssl_lookup, token_checks,
        dry_run: bool = False, say=log) -> dict:
    """One pass. Everything that touches the outside world is passed in, so the
    offline test can run this exact function against fakes."""
    db = cfg["database_id"]
    items = [it for it in map(parse_item, notion.query_database(db)) if it.name or it.key]
    writes: dict[str, dict] = {}

    def put(item: Item, prop: str, value: dict) -> None:
        if item.page_id:
            writes.setdefault(item.page_id, {})[prop] = value

    # --- automatic checks ---
    wanted: list[checks_mod.Check] = []
    known: set[str] = set()
    hosts_done: set[str] = set()
    for it in items:
        if it.type != rules.T_DOMAIN or it.key:
            continue
        host = checks_mod.host_of(it.name)
        if not host:
            if not it.expires:
                it.note = NOT_A_HOST
            continue
        known.add(f"ssl:{host}")
        if it.paused:
            continue
        found, note = domain_lookup(host)
        if found:
            if found != it.expires:
                it.expires = found
                put(it, P_EXPIRES, date_prop(found))
        elif not it.expires:
            it.note = note
        if host not in hosts_done:
            hosts_done.add(host)
            wanted.append(ssl_lookup(host))

    token_results, unchecked = token_checks(cfg)
    wanted += token_results

    by_key = {it.key: it for it in items if it.key}
    created, unknown = [], 0
    for c in wanted:
        known.add(c.key)
        it = by_key.get(c.key)
        if it is None:
            page_id = None
            if not dry_run:
                page_id = notion.create_page({
                    "parent": {"database_id": db},
                    "properties": new_row(c.name, c.type, key=c.key, expires=c.expires),
                })["id"]
            it = Item(page_id=page_id, name=c.name, type=c.type, expires=c.expires, key=c.key)
            items.append(it)
            by_key[c.key] = it
            created.append(c.name)
        if it.paused:
            continue
        if c.expires and c.expires != it.expires:
            it.expires = c.expires
            put(it, P_EXPIRES, date_prop(c.expires))
        if c.state == checks_mod.PROBLEM:
            it.problem = c.detail
        else:
            it.note = c.detail or None
            it.healthy = c.state == checks_mod.OK
        if c.state == checks_mod.UNKNOWN:
            unknown += 1

    # --- what needs an alert ---
    alerts, alert_marks, upcoming, no_date = [], [], [], 0
    for it in items:
        if it.paused:
            continue
        if it.key and it.key not in known:
            if it.status != ORPHAN_STATUS:
                put(it, P_STATUS, text_prop(ORPHAN_STATUS))
            continue
        auto = rules.renews_itself(it.auto_renew, it.repeats)
        if it.expires and auto and it.expires < today:
            it.expires = rules.roll_forward(it.expires, it.repeats, today)
            put(it, P_EXPIRES, date_prop(it.expires))

        days = stage_name = mark = None
        if it.expires:
            days = (it.expires - today).days
            warn = rules.parse_warn(it.warn_text) or rules.default_warn(it.type, it.repeats, auto)
            stage_name = rules.stage(days, warn)
        if it.problem:
            mark = rules.problem_marker(today)
        elif stage_name:
            mark = rules.marker(it.expires, stage_name)

        if mark and mark != it.alerted:
            alerts.append({"name": it.name, "type": it.type, "expires": it.expires, "days_left": days,
                           "auto": auto, "problem": it.problem, "cost": it.cost, "link": it.link,
                           "notes": it.notes})
            alert_marks.append((it, mark))
        elif not mark and it.alerted:
            put(it, P_ALERTED, text_prop(""))

        status = rules.status_text(problem=it.problem, note=it.note, expires=it.expires, days_left=days,
                                   stage_name=stage_name, auto=auto, healthy=it.healthy)
        if status != it.status:
            put(it, P_STATUS, text_prop(status))

        if it.expires and days >= 0:
            upcoming.append({"name": it.name, "expires": it.expires, "days_left": days, "auto": auto})
        elif not it.expires and not it.key and not it.note:
            no_date += 1
    upcoming.sort(key=lambda u: u["days_left"])

    # --- write and send ---
    if dry_run:
        for name in created:
            say(f"[dry run] would add a row: {name}")
        say(f"[dry run] would update {len(writes)} row(s) in Notion")
    else:
        for page_id, props in writes.items():
            notion.update_page(page_id, props)

    if alerts:
        text = rules.format_digest(alerts, today)
        if dry_run:
            say("[dry run] would send to Telegram:\n" + text)
        elif send is None:
            # No marker is written, so these go out on the first run after Telegram is set up.
            say(f"{len(alerts)} alert(s) are waiting until Telegram is set up.")
        else:
            send(text)
            # Only now: if sending failed above, the next run tries these alerts again.
            for it, mark in alert_marks:
                if it.page_id:
                    notion.update_page(it.page_id, {P_ALERTED: text_prop(mark)})

    return {"items": len(items), "alerts": len(alerts), "created": created, "upcoming": upcoming,
            "no_date": no_date, "unknown": unknown, "unchecked": unchecked}


# --- command line -------------------------------------------------------------

def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def week_id(today: date) -> str:
    """Weeks start on Sunday here."""
    year, week, _ = (today + timedelta(days=1)).isocalendar()
    return f"{year}-W{week:02d}"


def safe(text: str) -> str:
    """Error text for the log or a message: first line, with anything token-shaped removed."""
    first = (str(text).strip().splitlines() or [""])[0][:300]
    return re.sub(r"bot\d+:[\w-]+|[A-Za-z0-9_\-]{32,}", "[hidden]", first)


def main() -> int:
    parser = argparse.ArgumentParser(description="Warns on Telegram before subscriptions, domains and keys run out.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen; send and change nothing")
    parser.add_argument("--if-due", action="store_true", help="Do nothing if today's run already succeeded")
    parser.add_argument("--test-message", action="store_true", help="Send a test message to Telegram and stop")
    parser.add_argument("--heartbeat", action="store_true", help="Send the weekly 'still running' note now")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    today = date.today()
    state = load_state()
    if args.if_due and state.get("last_ok") == today.isoformat():
        return 0

    try:
        cfg = load_config()
    except NotionError as exc:
        log(str(exc))
        return 2

    sender = None
    try:
        token, chat_id = telegram_send.credentials(cfg)
        sender = lambda text: telegram_send.send(text, token, chat_id)  # noqa: E731
    except telegram_send.TelegramError as exc:
        # The list in Notion is still kept up to date; alerts wait until Telegram works.
        log(str(exc))

    if args.test_message:
        if not sender:
            return 2
        sender("✅ <b>Test from the renewal check</b>\nAlerts about subscriptions, domains and keys "
               "will arrive here.")
        log("Test message sent.")
        return 0

    try:
        summary = run(Notion(), cfg, today, send=sender, domain_lookup=checks_mod.domain_lookup,
                      ssl_lookup=checks_mod.ssl_lookup, token_checks=checks_mod.token_checks,
                      dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 - under pythonw a crash would otherwise vanish
        frames = "".join(traceback.format_tb(exc.__traceback__)[-3:])
        log(f"Run failed: {type(exc).__name__}: {safe(exc)}\n{frames}")
        # One quiet failure is normal (no internet at 9:00); the task tries again in a few
        # hours. Two days without a good run is worth a message.
        last_ok = state.get("last_ok")
        stale = not last_ok or (today - date.fromisoformat(last_ok)).days >= 2
        if sender and stale and not args.dry_run and state.get("fail_notice") != today.isoformat():
            try:
                sender(f"⚠️ <b>The renewal check couldn't run</b>\n{safe(exc)}\n"
                       f"Last good run: {last_ok or 'never'}.")
                state["fail_notice"] = today.isoformat()
                save_state(state)
            except telegram_send.TelegramError:
                pass
        return 1

    sent_word = "sent" if sender and not args.dry_run else "to send"
    log(f"Checked {summary['items']} item(s): {summary['alerts']} alert(s) {sent_word}"
        + (f", {len(summary['created'])} row(s) added" if summary["created"] else "")
        + (f", {summary['unknown']} check(s) couldn't be done" if summary["unknown"] else ""))
    if args.dry_run:
        for u in summary["upcoming"][:10]:
            log(f"  {u['days_left']:>5} days  {u['name']}")
        if summary["unchecked"]:
            log("No automatic test for: " + ", ".join(summary["unchecked"]))
        return 0
    if not sender:
        return 2  # not a finished run: the next trigger tries again

    state["last_ok"] = today.isoformat()
    if args.heartbeat or state.get("heartbeat_week") != week_id(today):
        try:
            sender(rules.format_heartbeat(summary["upcoming"], summary["no_date"], summary["unknown"], today))
            state["heartbeat_week"] = week_id(today)
        except telegram_send.TelegramError as exc:
            log(f"Weekly note not sent: {safe(exc)}")
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
