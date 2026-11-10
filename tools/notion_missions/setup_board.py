"""
Creates the Claude Missions board inside a Notion page you shared with the
integration: a short how-to at the top, the missions database, and one
example mission (left as Draft, so it never runs).

Usage:
    python tools/notion_missions/setup_board.py <notion page link or id> [--force]

Writes tools/notion_missions/board.json (database id, your Notion user id).
"""

import argparse
import sys
from pathlib import Path

import live
from board import (CONFIG_PATH, DRAFT, P_MISSION, P_PRIORITY, P_PROJECT, P_STATUS,
                   create_board_view, database_schema, save_config)
from notion_api import Notion, NotionError, block, page_id_from, rich_text

TIP = ("The Board view shows each mission's stage. The Live status box right above it shows "
       "what Claude is working on right now, what's waiting and what's finished.")

HOW_TO = [
    "Add a row: the mission as its name, the Project, and details in the page if needed "
    "(screenshots and links are welcome). That's all. Claude picks it up on its next hourly run, "
    "once you haven't edited it for 10 minutes.",
    "Not ready yet? Set Status to Draft and it's left alone. Set Ready to skip the 10-minute wait.",
    "Claude works on a separate branch and writes a report into the mission's page. It never "
    "pushes, deploys, sends messages or spends paid credits.",
    "Needs review: check the work, then ask Claude in a session to ship it, and set Done. "
    "Needs info: answer the questions at the bottom of the page and set Ready again.",
]

EXAMPLE_BODY = [
    ("paragraph", "This is an example. It stays a Draft, so Claude won't run it. "
                  "Delete it whenever you like."),
    ("heading_3", "What I want"),
    ("paragraph", "On the Plumb settings page, add a switch that turns dark mode on and off, "
                  "and remember the choice."),
    ("heading_3", "Where"),
    ("paragraph", "Settings page, top right of the header."),
    ("heading_3", "Done when"),
    ("bulleted_list_item", "The switch changes the theme straight away."),
    ("bulleted_list_item", "The choice is still there after a refresh."),
    ("heading_3", "Don't"),
    ("bulleted_list_item", "Don't change the colours of the existing light theme."),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("page", help="Link (or id) of the Notion page to build the board in")
    parser.add_argument("--force", action="store_true", help="Build a new board even if one exists")
    args = parser.parse_args()

    notion = Notion()
    if CONFIG_PATH.exists() and not args.force:
        sys.exit(f"A board already exists ({CONFIG_PATH}). Use --force to build another one.")

    page_id = page_id_from(args.page)
    try:
        page = notion.get_page(page_id)
    except NotionError as exc:
        sys.exit(f"Can't open that page: {exc}\nIn Notion, open the page, click ... > Connections, "
                 f"and add your integration.")
    bot = notion.me()
    owner_id = page["created_by"]["id"]

    cfg = {
        "parent_page_id": page_id,
        "owner_ids": [owner_id],
        "bot_id": bot["id"],
        "extra_projects": {},
    }
    lifemaxing = Path.home() / "lifemaxing"
    if lifemaxing.is_dir():
        cfg["extra_projects"]["lifemaxing"] = str(lifemaxing)

    notion.append(page_id, [
        block("callout", "How this board works", icon={"type": "emoji", "emoji": "🤖"}, color="gray_background"),
        *[block("numbered_list_item", line) for line in HOW_TO],
        block("paragraph", TIP),
    ])

    db = notion.create_database({
        "parent": {"type": "page_id", "page_id": page_id},
        "is_inline": True,
        "title": rich_text("Missions"),
        "properties": database_schema(cfg),
    })
    cfg["database_id"] = db["id"]
    cfg["database_url"] = db.get("url", "")

    notion.create_page({
        "parent": {"database_id": db["id"]},
        "icon": {"type": "emoji", "emoji": "📝"},
        "properties": {
            P_MISSION: {"title": rich_text("Example: dark-mode switch on the Plumb settings page")},
            P_STATUS: {"select": {"name": DRAFT}},
            P_PROJECT: {"select": {"name": "plumb"}},
            P_PRIORITY: {"select": {"name": "Normal"}},
        },
        "children": [block(kind, text) for kind, text in EXAMPLE_BODY],
    })

    save_config(cfg)
    try:
        create_board_view(notion, cfg)
    except NotionError as exc:
        print(f"Couldn't add the Board view ({exc}). Switch the table to Board grouped by Status by hand.")
    live.refresh(notion, cfg)  # creates the Live status box above the board
    print(f"Board created: {cfg['database_url'] or db['id']}")
    print(f"Owner (only missions you edited last will run): {owner_id}")
    print(f"Saved {CONFIG_PATH}")


if __name__ == "__main__":
    try:
        main()
    except NotionError as exc:
        sys.exit(str(exc))
