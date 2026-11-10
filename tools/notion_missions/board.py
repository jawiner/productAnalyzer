"""
Shared definitions for the Claude Missions board: property names, statuses,
the project list, the local board config and reading a mission page as text.
"""

import json
import mimetypes
import re
from pathlib import Path

import requests

from notion_api import ROOT, Notion, NotionError, plain

CONFIG_PATH = Path(__file__).resolve().parent / "board.json"  # gitignored, not secret
STATE_DIR = ROOT / ".tmp" / "notion_missions"
MEMORY_DIR = Path.home() / ".claude" / "projects" / "c--Users-97254-wat-framework" / "memory"

# Property names on the board
P_MISSION = "Mission"
P_STATUS = "Status"
P_PROJECT = "Project"
P_PRIORITY = "Priority"
P_RESULT = "Result"
P_BRANCH = "Branch"
P_LAST_RUN = "Last run"

DRAFT, READY, RUNNING = "Draft", "Ready", "Running"
NEEDS_INFO, NEEDS_REVIEW, DONE, FAILED = "Needs info", "Needs review", "Done", "Failed"
STATUSES = [(DRAFT, "gray"), (READY, "blue"), (RUNNING, "yellow"), (NEEDS_INFO, "orange"),
            (NEEDS_REVIEW, "purple"), (DONE, "green"), (FAILED, "red")]
PRIORITIES = [("High", "red"), ("Normal", "default"), ("Low", "gray")]

NO_PROJECT = "No project (research / writing)"
NEW_PROJECT = "New project"
WORKSPACE = "wat-framework"
CATEGORIES = ("websites", "saas", "internal")


# --- local config ----------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise NotionError(
            f"No board yet ({CONFIG_PATH.name} missing). Run setup_board.py with your Notion page link first."
        )
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# --- projects --------------------------------------------------------------

def list_projects(cfg: dict | None = None) -> dict[str, Path]:
    """Project name -> folder. Category folders win over same-named root folders;
    extra_projects in board.json add outside projects and override the scan
    (e.g. barukh-law, whose repo is its site/ subfolder)."""
    projects: dict[str, Path] = {WORKSPACE: ROOT}
    for category in CATEGORIES:
        for folder in sorted((ROOT / category).glob("*")):
            if folder.is_dir() and not folder.name.startswith("."):
                projects.setdefault(folder.name, folder)
    for folder in sorted(ROOT.iterdir()):
        if folder.is_dir() and (folder / ".git").exists():
            projects.setdefault(folder.name, folder)
    for name, path in ((cfg or {}).get("extra_projects") or {}).items():
        if Path(path).is_dir():
            projects[name] = Path(path)
    return projects


def project_options(cfg: dict | None = None) -> list[dict]:
    names = [NO_PROJECT, NEW_PROJECT] + sorted(list_projects(cfg), key=str.lower)
    return [{"name": n} for n in names]


def database_schema(cfg: dict | None = None) -> dict:
    return {
        P_MISSION: {"title": {}},
        P_STATUS: {"select": {"options": [{"name": n, "color": c} for n, c in STATUSES]}},
        P_PROJECT: {"select": {"options": project_options(cfg)}},
        P_PRIORITY: {"select": {"options": [{"name": n, "color": c} for n, c in PRIORITIES]}},
        P_RESULT: {"rich_text": {}},
        P_BRANCH: {"rich_text": {}},
        P_LAST_RUN: {"date": {}},
    }


def sync_project_options(notion: Notion, cfg: dict) -> None:
    """Adds newly created project folders to the Project dropdown."""
    db = notion.get_database(cfg["database_id"])
    existing = {o["name"] for o in db["properties"].get(P_PROJECT, {}).get("select", {}).get("options", [])}
    missing = [o for o in project_options(cfg) if o["name"] not in existing]
    if missing:
        current = db["properties"][P_PROJECT]["select"]["options"]
        notion.update_database(cfg["database_id"], {
            "properties": {P_PROJECT: {"select": {"options": [{"name": o["name"]} for o in current] + missing}}}
        })


# --- page properties ---------------------------------------------------------

PRIORITY_RANK = {"High": 0, "Normal": 1, "": 1, "Low": 2}


def queue_order(pages: list[dict]) -> list[dict]:
    """High priority first, then oldest."""
    return sorted(pages, key=lambda p: (PRIORITY_RANK.get(prop_text(p, P_PRIORITY), 1), p["created_time"]))


def is_trusted(page: dict, cfg: dict) -> bool:
    """Last edited by you, or by this integration on your behalf (only your own tools hold its token)."""
    editor = (page.get("last_edited_by") or {}).get("id")
    return editor in set(cfg.get("owner_ids", [])) | {cfg.get("bot_id")}


def create_board_view(notion: Notion, cfg: dict) -> str:
    """Adds a Board view grouped by Status as the first view of the missions database."""
    props = notion.get_database(cfg["database_id"])["properties"]
    view = notion.create_view({
        "database_id": cfg["database_id"],
        "data_source_id": notion.data_source_id(cfg["database_id"]),
        "name": "Board",
        "type": "board",
        "position": {"type": "start"},
        "configuration": {
            "type": "board",
            "group_by": {"type": "select", "property_id": props[P_STATUS]["id"],
                         "sort": {"type": "manual"}, "hide_empty_groups": False},
            "properties": [{"property_id": props[n]["id"], "visible": True}
                           for n in (P_PROJECT, P_RESULT, P_LAST_RUN, P_PRIORITY)]
                          + [{"property_id": props[P_BRANCH]["id"], "visible": False}],
        },
    })
    cfg["board_view_id"] = view["id"]
    save_config(cfg)
    return view["id"]


def prop_text(page: dict, name: str) -> str:
    prop = page["properties"].get(name) or {}
    kind = prop.get("type")
    if kind in ("title", "rich_text"):
        return plain(prop[kind]).strip()
    if kind == "select":
        return (prop["select"] or {}).get("name", "")
    return ""


# --- reading a mission page ----------------------------------------------------

def _download(url: str, folder: Path, stem: str, caption: str) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        ext = Path(url.split("?")[0]).suffix or mimetypes.guess_extension(r.headers.get("Content-Type", "")) or ""
        target = folder / f"{stem}{ext[:8]}"
        size = 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(65536):
                size += len(chunk)
                if size > 25 * 1024 * 1024:
                    raise ValueError("bigger than 25 MB")
                f.write(chunk)
        return f"[attachment saved at {target}{' - ' + caption if caption else ''}]"
    except Exception as exc:  # an attachment must never stop the mission
        return f"[attachment {url.split('?')[0]} could not be downloaded: {exc}]"


def page_text(notion: Notion, block_id: str, attachments: Path, depth: int = 0, counter: list | None = None) -> str:
    """The page body as plain text, with images and files downloaded into `attachments`."""
    counter = counter if counter is not None else [0]
    lines = []
    indent = "  " * depth
    for b in notion.children(block_id):
        kind = b["type"]
        data = b.get(kind, {})
        text = plain(data.get("rich_text", []))
        if kind in ("image", "file", "pdf", "video"):
            counter[0] += 1
            source = data.get(data.get("type", ""), {}) or {}
            caption = plain(data.get("caption", []))
            line = _download(source["url"], attachments, f"{counter[0]:02d}-{kind}", caption) if source.get("url") else ""
        elif kind.startswith("heading_"):
            line = "#" * int(kind[-1]) + " " + text
        elif kind == "bulleted_list_item":
            line = "- " + text
        elif kind == "numbered_list_item":
            line = "1. " + text
        elif kind == "to_do":
            line = f"- [{'x' if data.get('checked') else ' '}] {text}"
        elif kind == "quote":
            line = "> " + text
        elif kind == "code":
            line = f"```{data.get('language', '')}\n{text}\n```"
        elif kind == "divider":
            line = "---"
        elif kind == "bookmark" or kind == "embed" or kind == "link_preview":
            line = data.get("url", "")
        elif kind in ("child_page", "child_database"):
            line = f"[sub-page: {data.get('title', '')}]"
        else:
            line = text
        if line:
            lines.append(indent + line)
        if b.get("has_children") and depth < 3 and kind not in ("child_page", "child_database"):
            nested = page_text(notion, b["id"], attachments, depth + 1, counter)
            if nested:
                lines.append(nested)
    return "\n".join(lines)


def find_database(notion: Notion, cfg: dict) -> str:
    db_id = cfg.get("database_id")
    if not db_id:
        raise NotionError("board.json has no database_id. Run setup_board.py again.")
    try:
        notion.get_database(db_id)
    except NotionError as exc:
        raise NotionError(
            f"Can't open the missions board ({exc}). Was it deleted, or the page un-shared from the integration?"
        ) from exc
    return db_id


def short_id(page_id: str) -> str:
    """Unique short form of a page id. The END of the id: pages in one workspace share
    a long common prefix (e.g. all of ours start 3febc2789f1d81...)."""
    return page_id.replace("-", "")[-10:]


def slug(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-")
