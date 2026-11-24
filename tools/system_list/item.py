"""
Keep the System list current from a terminal or a Claude session.

    python tools/system_list/item.py add "Shop site" "Turn on online payments" --priority P1 --who You
            [--kind Fix] [--due 2026-12-24] [--remind 2026-12-01] [--why "..."] [--source "..."]
    python tools/system_list/item.py seed .tmp/system_list/seed.json   # many at once (a JSON list)
    python tools/system_list/item.py done "online payments" [--system "Shop site"]
    python tools/system_list/item.py update "online payments" [--system "Shop site"] [--status Waiting]
            [--remind 2026-12-01] [--due ...] [--priority P0] [--who Claude]
    python tools/system_list/item.py list [--system "Shop site"] [--all]

add and seed skip a row that already exists (same system and same words).
done and update change a row only when the words match exactly one open row.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from todo_table import (P_DUE, P_PRIORITY, P_REMIND, P_STATUS, P_WHO, PRIORITIES, STATUSES, WHO, Item,
                        Notion, NotionError, date_prop, load_config, new_row, normalise, read_all, same,
                        select_prop)


def add_items(notion, db_id: str, raws: list[dict], existing=None, *, say=print) -> tuple[int, int]:
    existing = list(existing if existing is not None else read_all(notion, db_id))
    added = skipped = 0
    for raw in raws:
        item = normalise(raw)
        if not item["item"]:
            continue
        if any(same(e.item, item["item"]) and same(e.system, item["system"]) for e in existing):
            skipped += 1
            continue
        page = notion.create_page({"parent": {"database_id": db_id}, "properties": new_row(item)})
        existing.append(Item(page_id=page.get("id"), item=item["item"], system=item["system"]))
        added += 1
    say(f"Added {added} row(s)" + (f", skipped {skipped} already on the list" if skipped else "") + ".")
    return added, skipped


def find_open(items, words: str, system: str | None):
    words = words.lower()
    return [it for it in items if it.open and words in it.item.lower()
            and (not system or same(it.system, system))]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Add, finish or list rows on the System list.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("system")
    a.add_argument("item")
    for flag in ("kind", "priority", "who", "status", "due", "remind", "why", "source"):
        a.add_argument(f"--{flag}")

    s = sub.add_parser("seed")
    s.add_argument("file")

    for name in ("done", "update"):
        u = sub.add_parser(name)
        u.add_argument("words")
        u.add_argument("--system")
        if name == "update":
            u.add_argument("--status", choices=STATUSES)
            u.add_argument("--priority", choices=PRIORITIES)
            u.add_argument("--who", choices=WHO)
            u.add_argument("--remind", type=date.fromisoformat)
            u.add_argument("--due", type=date.fromisoformat)

    lst = sub.add_parser("list")
    lst.add_argument("--system")
    lst.add_argument("--all", action="store_true", help="Include Done and Parked rows")
    args = parser.parse_args()

    cfg = load_config()
    notion = Notion()
    db = cfg["database_id"]

    if args.cmd == "add":
        add_items(notion, db, [{k: getattr(args, k) for k in
                                ("system", "item", "kind", "priority", "who", "status", "due",
                                 "remind", "why", "source")}])
        return 0
    if args.cmd == "seed":
        raws = json.loads(Path(args.file).read_text(encoding="utf-8"))
        add_items(notion, db, raws)
        return 0

    items = read_all(notion, db)
    if args.cmd == "list":
        rows = [it for it in items if (args.all or it.open)
                and (not args.system or same(it.system, args.system))]
        for it in sorted(rows, key=lambda it: (it.system, it.rank, it.item)):
            due = f"  due {it.due}" if it.due else ""
            print(f"{it.priority or '--'}  {it.status:<8} {it.system}: {it.item}{due}")
        print(f"{len(rows)} row(s).")
        return 0

    matches = find_open(items, args.words, args.system)
    if len(matches) != 1:
        print(f"{len(matches)} open rows match, so nothing was changed." if matches else
              "No open row matches those words.")
        for it in matches[:15]:
            print(f"  {it.system}: {it.item}")
        return 1
    it = matches[0]
    props = {}
    if args.cmd == "done":
        props[P_STATUS] = select_prop("Done")
    else:
        if args.status:
            props[P_STATUS] = select_prop(args.status)
        if args.priority:
            props[P_PRIORITY] = select_prop(args.priority)
        if args.who:
            props[P_WHO] = select_prop(args.who)
        if args.remind:
            props[P_REMIND] = date_prop(args.remind)
        if args.due:
            props[P_DUE] = date_prop(args.due)
    if not props:
        print("Nothing to change: give --status, --priority, --who, --remind or --due.")
        return 1
    notion.update_page(it.page_id, props)
    print(f"Updated: {it.system}: {it.item}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NotionError as exc:
        sys.exit(str(exc))
