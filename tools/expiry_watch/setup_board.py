"""
One-time: builds the Renewals page and table in Notion and writes board.json.

Usage:
    python tools/expiry_watch/setup_board.py [notion page link] [--force]

Without a link, the page is created inside the page the missions board already
lives in (the integration can only write where it has been given access).
"""

import argparse
import json
import sys

import rules
from renewals import (CONFIG_PATH, DAYS_FORMULA, MISSIONS_CONFIG, P_DAYS, Notion, NotionError, block,
                      database_schema, new_row, page_id_from, rich_text, save_config)

HOW_TO = [
    "Add a row for anything with an end date: a subscription, a licence, a membership, a key. "
    "Give it a name and the date in Expires. That's enough.",
    "Each morning the check looks at every row and writes to you on Telegram 30, 14, 7, 3 and 1 "
    "days before the date, on the day, and after it if nothing changed. To choose other days, "
    "type them in 'Warn days before' (for example: 60, 30, 7).",
    "Pays by itself? Tick 'Renews by itself' and set Repeats. You then get a short heads-up before "
    "each charge (time to cancel), and the date moves on by itself afterwards.",
    "Type = Domain: write the address as the name (example.co.il) and leave the date empty. The "
    "real date is read from the registry, and the site's certificate gets its own row.",
    "Rows with something in 'Auto key' are added by the check itself (certificates, API keys in "
    ".env). Status says whether each key still works.",
    "Renewed something? Change its date. Don't want to hear about a row? Tick Paused.",
]

SEED_DOMAINS = ["castly.cloud", "mashtech.co.il"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("page", nargs="?", help="Link (or id) of a Notion page shared with the integration")
    parser.add_argument("--force", action="store_true", help="Build a new table even if one exists")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    if CONFIG_PATH.exists() and not args.force:
        sys.exit(f"The table already exists ({CONFIG_PATH}). Use --force to build another one.")

    notion = Notion()
    if args.page:
        parent_id = page_id_from(args.page)
    elif MISSIONS_CONFIG.exists():
        parent_id = json.loads(MISSIONS_CONFIG.read_text(encoding="utf-8"))["parent_page_id"]
    else:
        sys.exit("Give the link of a Notion page that is shared with the integration "
                 "(open the page > ... > Connections > add the integration).")

    try:
        page = notion.create_page({
            "parent": {"type": "page_id", "page_id": parent_id},
            "icon": {"type": "emoji", "emoji": "⏰"},
            "properties": {"title": {"title": rich_text("Renewals")}},
        })
    except NotionError as exc:
        sys.exit(f"Can't create the page there: {exc}")
    page_id = page["id"]

    notion.append(page_id, [
        block("callout", "How this list works", icon={"type": "emoji", "emoji": "⏰"}, color="gray_background"),
        *[block("numbered_list_item", line) for line in HOW_TO],
    ])

    db = notion.create_database({
        "parent": {"type": "page_id", "page_id": page_id},
        "is_inline": True,
        "title": rich_text("Renewals"),
        "properties": database_schema(),
    })
    try:
        notion.update_database(db["id"], {"properties": {P_DAYS: {"formula": {"expression": DAYS_FORMULA}}}})
    except NotionError as exc:
        print(f"Couldn't add the 'Days left' column ({exc}). The check works without it.")

    for domain in SEED_DOMAINS:
        notion.create_page({"parent": {"database_id": db["id"]},
                            "properties": new_row(domain, rules.T_DOMAIN)})
    notion.create_page({
        "parent": {"database_id": db["id"]},
        "properties": new_row("Example: design tool subscription", rules.T_SUBSCRIPTION, paused=True,
                              repeats=rules.R_MONTHLY, auto=True, cost="$20 / month",
                              notes="An example row. It's paused, so it never alerts. Delete it whenever."),
    })

    save_config({
        "page_id": page_id,
        "page_url": page.get("url", ""),
        "database_id": db["id"],
        "database_url": db.get("url", ""),
        "extra_env_files": [],
    })
    print(f"Renewals page created: {page.get('url') or page_id}")
    print(f"Saved {CONFIG_PATH}")


if __name__ == "__main__":
    try:
        main()
    except NotionError as exc:
        sys.exit(str(exc))
