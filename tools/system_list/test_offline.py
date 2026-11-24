"""
Offline test of the System list: fake Notion, fake Telegram. Touches nothing real, sends nothing.

    python tools/system_list/test_offline.py
"""

import sys
from datetime import date, timedelta

import item as item_cli
import remind
from todo_table import (P_PINGED, P_STATUS, Item, new_row, normalise, parse_item, read_all)

passed = failed = 0


def check(label: str, condition: bool, got=None) -> None:
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"FAIL  {label}" + (f"  (got {got!r})" if got is not None else ""))


class FakeNotion:
    """Stores pages as Notion would return them (property values in API shape)."""

    def __init__(self):
        self.pages: dict[str, dict] = {}
        self.count = 0
        self.updates = 0

    def _page(self, pid, props):
        page = {"id": pid, "properties": {}}
        for name, value in props.items():
            if "title" in value:
                page["properties"][name] = {"title": [{"plain_text": t["text"]["content"]} for t in value["title"]]}
            elif "rich_text" in value:
                page["properties"][name] = {"rich_text": [{"plain_text": t["text"]["content"]}
                                                          for t in value["rich_text"]]}
            else:
                page["properties"][name] = value
        return page

    def add(self, **raw) -> str:
        pinged = raw.pop("pinged", None)
        page = self.create_page({"parent": {"database_id": "db"}, "properties": new_row(normalise(raw))})
        if pinged:
            self.pages[page["id"]]["properties"][P_PINGED] = {"date": {"start": pinged.isoformat()}}
        return page["id"]

    def create_page(self, body):
        self.count += 1
        pid = f"p{self.count}"
        self.pages[pid] = self._page(pid, body["properties"])
        return self.pages[pid]

    def update_page(self, pid, props):
        self.updates += 1
        self.pages[pid]["properties"].update(self._page(pid, props)["properties"])

    def query_database(self, db_id):
        return list(self.pages.values())


TODAY = date(2026, 11, 29)  # a Sunday
CFG = {"database_id": "db", "page_url": "https://notion.so/system-list"}


def item(**kw) -> Item:
    base = dict(page_id="x", item="Do the thing", system="Shop site", priority="P2", status="To do")
    base.update(kw)
    return Item(**base)


# --- ping rules -------------------------------------------------------------------
r = remind.ping_reason
check("no dates, no ping", r(item(), TODAY) is None)
check("remind today pings", r(item(remind=TODAY), TODAY) == "remind")
check("remind in the past, never pinged, pings", r(item(remind=TODAY - timedelta(days=3)), TODAY) == "remind")
check("remind already pinged on that date doesn't", r(item(remind=TODAY, pinged=TODAY), TODAY) is None)
check("remind in the future doesn't", r(item(remind=TODAY + timedelta(days=1)), TODAY) is None)
check("snoozed past the last ping pings again",
      r(item(remind=TODAY, pinged=TODAY - timedelta(days=5)), TODAY) == "remind")
check("Done never pings", r(item(remind=TODAY, status="Done"), TODAY) is None)
check("Parked never pings", r(item(due=TODAY, status="Parked"), TODAY) is None)
check("Waiting still pings", r(item(remind=TODAY, status="Waiting"), TODAY) == "remind")
due = TODAY + timedelta(days=7)
check("due in 7 days pings", r(item(due=due), TODAY) == "due")
check("due in 8 days doesn't", r(item(due=TODAY + timedelta(days=8)), TODAY) is None)
check("due in 5 days, pinged at 7, doesn't",
      r(item(due=TODAY + timedelta(days=5), pinged=TODAY - timedelta(days=2)), TODAY) is None)
check("due tomorrow, pinged a week before, pings",
      r(item(due=TODAY + timedelta(days=1), pinged=TODAY - timedelta(days=6)), TODAY) == "due")
check("due tomorrow, pinged today, doesn't", r(item(due=TODAY + timedelta(days=1), pinged=TODAY), TODAY) is None)
check("overdue, never pinged, pings once", r(item(due=TODAY - timedelta(days=3)), TODAY) == "overdue")
check("overdue, pinged after the day before, doesn't",
      r(item(due=TODAY - timedelta(days=3), pinged=TODAY - timedelta(days=2)), TODAY) is None)

# --- normalise ----------------------------------------------------------------------
n = normalise({"item": "  Turn   on billing ", "system": "Blog", "who": "Waiting", "priority": "p1 soon",
               "status": "waiting on Meta", "kind": "Pay / renew", "due": "2026-12-24", "remind": "bad"})
check("spaces squeezed", n["item"] == "Turn on billing", n["item"])
check("Waiting → Someone else", n["who"] == "Someone else", n["who"])
check("priority read from 'p1 soon'", n["priority"] == "P1", n["priority"])
check("status 'waiting on Meta' → Waiting", n["status"] == "Waiting", n["status"])
check("due parsed", n["due"] == date(2026, 12, 24))
check("bad date dropped", n["remind"] is None)
n2 = normalise({"item": "x", "kind": "Whatever", "priority": "", "who": "Claude"})
check("unknown kind dropped", n2["kind"] == "")
check("missing priority → P2", n2["priority"] == "P2")
check("missing system → Other", n2["system"] == "Other")
check("Claude kept", n2["who"] == "Claude")

# --- add / seed skips duplicates ------------------------------------------------------
fake = FakeNotion()
added, skipped = item_cli.add_items(fake, "db", [
    {"system": "Shop site", "item": "Turn on online payments", "priority": "P1"},
    {"system": "shop site", "item": "turn on  online payments"},          # same, different case
    {"system": "Blog", "item": "Turn on online payments"},        # other system: new
    {"system": "Shop site", "item": ""},                                   # empty: ignored
], say=lambda *_: None)
check("two added", added == 2, added)
check("one skipped as a duplicate", skipped == 1, skipped)
added2, skipped2 = item_cli.add_items(fake, "db", [{"system": "Shop site", "item": "Turn on online payments"}],
                                      say=lambda *_: None)
check("second seed adds nothing", (added2, skipped2) == (0, 1), (added2, skipped2))
rows = read_all(fake, "db")
check("rows read back", len(rows) == 2 and rows[0].priority == "P1" and rows[0].status == "To do",
      [(x.item, x.priority, x.status) for x in rows])
check("find_open matches one", len(item_cli.find_open(rows, "online", "Shop site")) == 1)
check("find_open without system matches two", len(item_cli.find_open(rows, "online", None)) == 2)

# --- a full run: first run sends the summary, marks pings, no second message that day --------------
fake = FakeNotion()
urgent = fake.add(item="Fix the broken checkout button", system="Cafe site", priority="P0", who="Claude")
billing = fake.add(item="Renew the map plan <before> searches stop & fail", system="Sales tool",
                   priority="P1", who="You", due=(TODAY + timedelta(days=6)).isoformat())
later = fake.add(item="Look at the old logo", system="Blog", priority="P3")
nudged = fake.add(item="Call the first new customer", system="Shop site", priority="P1", who="You",
                  remind=TODAY.isoformat())
done = fake.add(item="Already finished", system="Shop site", priority="P0", status="Done")
late = fake.add(item="Pay the domain", system="Studio site", priority="P1", who="You",
                due=(TODAY - timedelta(days=2)).isoformat())

sent: list[str] = []
state: dict = {}
res = remind.run(fake, CFG, state, TODAY, send=sent.append, say=lambda *_: None)
check("one message on the first run", len(sent) == 1, len(sent))
msg = sent[0]
check("it is the weekly summary", res["summary"] and msg.startswith("🗂"), msg[:40])
check("open count excludes Done", "5 open items across 5 systems" in msg, msg.split("\n")[1])
check("only-you count", "3 only you can do" in msg, msg.split("\n")[1])
check("urgent section has the P0", "Fix the broken checkout button" in msg)
check("Done rows are left out", "Already finished" not in msg)
check("apostrophes stay plain", "&#x27;" not in msg)
check("HTML is escaped", "&lt;before&gt;" in msg and "&amp; fail" in msg and "<before>" not in msg)
check("overdue section", "⚠️ <b>Overdue</b>" in msg and "overdue since" in msg)
check("coming due section", "Coming due" in msg and "Renew the map plan" in msg)
check("today's reminder in the summary", "Call the first new customer" in msg)
check("P3 not listed by name", "Look at the old logo" not in msg)
check("counts per system", "📊" in msg and "Shop site 1" in msg, msg.split("📊")[-1][:80])
check("link at the end", 'href="https://notion.so/system-list"' in msg)
pinged = {pid for pid, p in fake.pages.items() if P_PINGED in p["properties"]}
check("pinged rows marked (remind, due in 6 days, overdue)", pinged == {billing, nudged, late}, pinged)
check("summary week saved", state.get("summary_week") == remind.week_id(TODAY))

res2 = remind.run(fake, CFG, state, TODAY, send=sent.append, say=lambda *_: None)
check("second run the same day sends nothing", len(sent) == 1 and not res2["sent"], len(sent))

# Monday: nothing new is due → silence. Snooze one to Tuesday → a reminder on Tuesday only.
monday = TODAY + timedelta(days=1)
remind.run(fake, CFG, state, monday, send=sent.append, say=lambda *_: None)
check("Monday: nothing to say, nothing sent", len(sent) == 1, len(sent))
fake.update_page(later, {"Remind on": {"date": {"start": (TODAY + timedelta(days=2)).isoformat()}}})
remind.run(fake, CFG, state, TODAY + timedelta(days=2), send=sent.append, say=lambda *_: None)
check("Tuesday: one reminder message", len(sent) == 2 and sent[-1].startswith("⏰"), sent[-1][:30])
check("…with the snoozed row in it", "Look at the old logo" in sent[-1])
check("…and not the summary", "📊" not in sent[-1])

# The billing row: due in 6 days was pinged on Sunday; the day before its due date it pings again.
day_before = TODAY + timedelta(days=5)
remind.run(fake, CFG, state, day_before, send=sent.append, say=lambda *_: None)
check("day before due: reminder", "Renew the map plan" in sent[-1] and sent[-1].startswith("⏰"))

# Next Sunday: a new summary even if nothing is due.
fake.update_page(urgent, {P_STATUS: {"select": {"name": "Done"}}})
remind.run(fake, CFG, state, TODAY + timedelta(days=7), send=sent.append, say=lambda *_: None)
check("next Sunday: a new summary", sent[-1].startswith("🗂"))
check("finished P0 gone from it", "Fix the broken checkout button" not in sent[-1])

# A failed send marks nothing, so the next run tries again.
fake2 = FakeNotion()
row = fake2.add(item="Try again", system="Shop site", remind=TODAY.isoformat())


def broken(_text):
    raise remind.telegram_send.TelegramError("Can't reach Telegram (ConnectionError)")


state2: dict = {}
try:
    remind.run(fake2, CFG, state2, TODAY, send=broken, say=lambda *_: None)
except remind.telegram_send.TelegramError:
    pass
check("failed send: row not marked", P_PINGED not in fake2.pages[row]["properties"])
check("failed send: summary week not saved", "summary_week" not in state2)

# A dry run sends and changes nothing.
fake3 = FakeNotion()
fake3.add(item="Dry", system="Shop site", remind=TODAY.isoformat())
said: list[str] = []
remind.run(fake3, CFG, {}, TODAY, send=None, dry_run=True, say=said.append)
check("dry run: shows the message", said and "would send" in said[0])
check("dry run: no writes", fake3.updates == 0)

# Long lists are cut with "+N more".
fake4 = FakeNotion()
for i in range(20):
    fake4.add(item=f"Urgent thing {i}", system=f"S{i % 3}", priority="P0")
out: list[str] = []
remind.run(fake4, CFG, {}, TODAY, send=out.append, say=lambda *_: None)
check("section capped", "…and 12 more in the list" in out[0], out[0][-200:])
check("message fits one Telegram message", len(out[0]) < 3900, len(out[0]))

# parse_item on a page with nothing but a title.
bare = parse_item({"id": "z", "properties": {"Item": {"title": [{"plain_text": "Bare"}]}}})
check("bare row defaults to To do and open", bare.status == "To do" and bare.open)

# Each script must import on its own in a fresh Python (the scheduled task runs remind.py alone).
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

for script in ("remind", "item", "setup_board"):
    proc = subprocess.run([sys.executable, "-c", f"import {script}"], cwd=Path(__file__).parent,
                          capture_output=True, text=True)
    check(f"{script}.py imports on its own", proc.returncode == 0, proc.stderr.strip()[-200:])

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
