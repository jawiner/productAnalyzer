"""
Builds the System list in Notion: a page with a short how-to and the table, next to the
Renewals list (inside the Claude Missions page, the one the integration can write to),
plus two board views: by system and by status.

    python tools/system_list/setup_board.py            # once
    python tools/system_list/setup_board.py <page link> # somewhere else
"""

import argparse
import json
import sys

from todo_table import (CONFIG_PATH, MISSIONS_CONFIG, P_DUE, P_PRIORITY, P_STATUS, P_SYSTEM, P_WHO, Notion,
                        NotionError, block, database_schema, page_id_from, rich_text, save_config)

HOW_TO = [
    "One row per thing to change, add, remove, finish, pay for or decide, across all your systems.",
    "Priority: P0 = a risk to users, money or the law right now · P1 = soon · P2 = normal · P3 = someday.",
    "Who: You = only you can do it · Claude = say “go” in a session · Someone else = waiting on another company.",
    "Finished? Set Status to Done. Parked = keep it on the list but stop reminding.",
    "Want a nudge on a certain day? Put a date in “Remind on”. A Due date also sends a reminder a week before and the day before.",
    "Every Sunday morning Telegram gets a summary: overdue and urgent items, what comes due soon and what only you can do.",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("page", nargs="?", help="Link (or id) of a Notion page shared with the integration")
    parser.add_argument("--force", action="store_true", help="Build a new table even if one exists")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    if CONFIG_PATH.exists() and not args.force:
        sys.exit(f"The System list already exists ({CONFIG_PATH}). Use --force to build another one.")

    notion = Notion()
    if args.page:
        parent_id = page_id_from(args.page)
    elif MISSIONS_CONFIG.exists():
        parent_id = json.loads(MISSIONS_CONFIG.read_text(encoding="utf-8"))["parent_page_id"]
    else:
        sys.exit("Give the link of a Notion page that is shared with the integration.")

    page = notion.create_page({
        "parent": {"type": "page_id", "page_id": parent_id},
        "icon": {"type": "emoji", "emoji": "🗂️"},
        "properties": {"title": {"title": rich_text("System list")}},
    })
    notion.append(page["id"], [
        block("callout", "How this list works", icon={"type": "emoji", "emoji": "🗂️"}, color="gray_background"),
        *[block("bulleted_list_item", line) for line in HOW_TO],
    ])
    db = notion.create_database({
        "parent": {"type": "page_id", "page_id": page["id"]},
        "is_inline": True,
        "title": rich_text("System list"),
        "properties": database_schema(),
    })
    cfg = {"page_id": page["id"], "page_url": page.get("url", ""),
           "database_id": db["id"], "database_url": db.get("url", "")}
    save_config(cfg)
    print(f"System list created: {cfg['page_url'] or cfg['page_id']}")

    # Board views are a nicety: the list and the reminders work without them.
    try:
        props = notion.get_database(db["id"])["properties"]
        source = notion.data_source_id(db["id"])
        for name, group in (("By system", P_SYSTEM), ("By status", P_STATUS)):
            shown = [n for n in (P_PRIORITY, P_WHO, P_DUE, P_STATUS, P_SYSTEM) if n != group]
            view = notion.create_view({
                "database_id": db["id"], "data_source_id": source, "name": name, "type": "board",
                "configuration": {
                    "type": "board",
                    "group_by": {"type": "select", "property_id": props[group]["id"],
                                 "sort": {"type": "manual"}, "hide_empty_groups": True},
                    "properties": [{"property_id": props[n]["id"], "visible": True} for n in shown],
                },
            })
            cfg[f"view_{group.lower()}"] = view["id"]
        save_config(cfg)
        print("Added the board views: By system, By status.")
    except (NotionError, KeyError) as exc:
        print(f"Couldn't add the board views ({exc}). The table works without them.")


if __name__ == "__main__":
    try:
        main()
    except NotionError as exc:
        sys.exit(str(exc))
