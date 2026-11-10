"""
Adds missions to the Claude Missions board from a JSON file.

Usage:
    python tools/notion_missions/add_missions.py missions.json [--draft]

missions.json is a list of {"title", "project", "body", "priority"?}. The body is
Markdown (it becomes the mission page). Missions are created Ready, so the next run
takes them; --draft parks them instead.
"""

import json
import sys

from board import (DRAFT, P_MISSION, P_PRIORITY, P_PROJECT, P_STATUS, PRIORITIES, READY,
                   find_database, load_config)
from notion_api import Notion, NotionError, markdown_to_blocks, rich_text


def main():
    args = [a for a in sys.argv[1:] if a != "--draft"]
    if len(args) != 1:
        sys.exit(__doc__)
    status = DRAFT if "--draft" in sys.argv else READY
    missions = json.loads(open(args[0], encoding="utf-8").read())
    cfg = load_config()
    notion = Notion()
    db_id = find_database(notion, cfg)
    db = notion.get_database(db_id)
    projects = {o["name"] for o in db["properties"][P_PROJECT]["select"]["options"]}
    priorities = {name for name, _ in PRIORITIES}

    for m in missions:  # check everything before creating anything
        if m.get("project") not in projects:
            sys.exit(f"Unknown project '{m.get('project')}' for '{m.get('title')}'. Known: {', '.join(sorted(projects))}")
        if m.get("priority", "Normal") not in priorities:
            sys.exit(f"Priority must be one of {', '.join(priorities)}")

    for m in missions:
        page = notion.create_page({
            "parent": {"database_id": db_id},
            "properties": {
                P_MISSION: {"title": rich_text(m["title"])},
                P_STATUS: {"select": {"name": status}},
                P_PROJECT: {"select": {"name": m["project"]}},
                P_PRIORITY: {"select": {"name": m.get("priority", "Normal")}},
            },
            "children": markdown_to_blocks(m.get("body", ""))[:100],
        })
        print(f"Added ({status}): {m['title']}  {page.get('url', '')}")


if __name__ == "__main__":
    try:
        main()
    except NotionError as exc:
        sys.exit(str(exc))
