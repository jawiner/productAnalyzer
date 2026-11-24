"""
The System list table in Notion: column names, schema, reading and writing a row, local config.

One row per thing to change, add, remove, finish, pay for or decide, across every system
the owner runs. remind.py reads it every morning and sends Telegram reminders.
"""

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
# Reuse the Notion client of the missions tool and the Telegram sender of the expiry watch.
# Appended (not inserted first), so this folder's own modules win over same-named ones there.
sys.path.append(str(HERE.parent / "notion_missions"))
sys.path.append(str(HERE.parent / "expiry_watch"))
from notion_api import Notion, NotionError, block, page_id_from, plain, rich_text  # noqa: E402,F401

CONFIG_PATH = HERE / "board.json"                       # gitignored: this machine's Notion ids
EXPIRY_CONFIG = HERE.parent / "expiry_watch" / "board.json"  # holds the Telegram chat id
MISSIONS_CONFIG = HERE.parent / "notion_missions" / "board.json"
STATE_DIR = ROOT / ".tmp" / "system_list"

P_ITEM = "Item"
P_SYSTEM = "System"
P_KIND = "Kind"
P_PRIORITY = "Priority"
P_WHO = "Who"
P_STATUS = "Status"
P_DUE = "Due"
P_REMIND = "Remind on"
P_WHY = "Why"
P_SOURCE = "Source"
P_PINGED = "Last reminder"

STATUSES = ["To do", "Doing", "Waiting", "Parked", "Done"]
CLOSED = {"Parked", "Done"}
KINDS = ["Fix", "Add", "Change", "Remove", "Finish & release", "Decide", "Pay / renew"]
PRIORITIES = ["P0", "P1", "P2", "P3"]
WHO = ["You", "Claude", "Someone else"]

STATUS_COLORS = {"To do": "gray", "Doing": "blue", "Waiting": "yellow", "Parked": "brown", "Done": "green"}
PRIORITY_COLORS = {"P0": "red", "P1": "orange", "P2": "yellow", "P3": "gray"}
WHO_COLORS = {"You": "purple", "Claude": "blue", "Someone else": "gray"}
KIND_COLORS = {"Fix": "red", "Add": "green", "Change": "blue", "Remove": "pink",
               "Finish & release": "purple", "Decide": "orange", "Pay / renew": "yellow"}


def _options(names: list[str], colors: dict[str, str]) -> dict:
    return {"options": [{"name": n, "color": colors.get(n, "default")} for n in names]}


def database_schema() -> dict:
    return {
        P_ITEM: {"title": {}},
        P_SYSTEM: {"select": {"options": []}},  # options appear as rows use them
        P_PRIORITY: {"select": _options(PRIORITIES, PRIORITY_COLORS)},
        P_STATUS: {"select": _options(STATUSES, STATUS_COLORS)},
        P_WHO: {"select": _options(WHO, WHO_COLORS)},
        P_KIND: {"select": _options(KINDS, KIND_COLORS)},
        P_DUE: {"date": {}},
        P_REMIND: {"date": {}},
        P_WHY: {"rich_text": {}},
        P_SOURCE: {"rich_text": {}},
        P_PINGED: {"date": {}},
    }


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise NotionError("The System list isn't set up yet. Run: python tools/system_list/setup_board.py")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def telegram_config() -> dict:
    """The expiry watch's config: the same bot writes to the same chat."""
    try:
        return json.loads(EXPIRY_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@dataclass
class Item:
    page_id: str | None
    item: str
    system: str = ""
    kind: str = ""
    priority: str = ""
    who: str = ""
    status: str = ""
    due: date | None = None
    remind: date | None = None
    why: str = ""
    source: str = ""
    pinged: date | None = None

    @property
    def open(self) -> bool:
        return self.status not in CLOSED

    @property
    def rank(self) -> int:
        return PRIORITIES.index(self.priority) if self.priority in PRIORITIES else len(PRIORITIES)


def _select(prop: dict | None) -> str:
    return ((prop or {}).get("select") or {}).get("name", "")


def _text(prop: dict | None) -> str:
    return plain((prop or {}).get("rich_text")).strip()


def _date(prop: dict | None) -> date | None:
    start = ((prop or {}).get("date") or {}).get("start")
    try:
        return date.fromisoformat(start[:10]) if start else None
    except ValueError:
        return None


def parse_item(page: dict) -> Item:
    p = page.get("properties", {})
    return Item(
        page_id=page["id"],
        item=plain((p.get(P_ITEM) or {}).get("title")).strip(),
        system=_select(p.get(P_SYSTEM)),
        kind=_select(p.get(P_KIND)),
        priority=_select(p.get(P_PRIORITY)),
        who=_select(p.get(P_WHO)),
        status=_select(p.get(P_STATUS)) or "To do",
        due=_date(p.get(P_DUE)),
        remind=_date(p.get(P_REMIND)),
        why=_text(p.get(P_WHY)),
        source=_text(p.get(P_SOURCE)),
        pinged=_date(p.get(P_PINGED)),
    )


def date_prop(d: date | None) -> dict:
    return {"date": {"start": d.isoformat()} if d else None}


def select_prop(name: str) -> dict:
    return {"select": {"name": name} if name else None}


def text_prop(text: str) -> dict:
    return {"rich_text": rich_text(text)}


def normalise(raw: dict) -> dict:
    """Cleans one item from a seed file or the command line into the table's vocabulary."""
    who = (raw.get("who") or "").strip()
    who = {"waiting": "Someone else", "third party": "Someone else", "owner": "You", "me": "You"}.get(
        who.lower(), who)
    status = (raw.get("status") or "To do").strip()
    if status not in STATUSES:
        status = "Waiting" if status.lower().startswith("wait") else "To do"
    kind = (raw.get("kind") or "").strip()
    priority = (raw.get("priority") or "").strip().upper()[:2]

    def day(value) -> date | None:
        try:
            return date.fromisoformat(str(value)[:10]) if value else None
        except ValueError:
            return None

    return {
        "item": " ".join(str(raw.get("item") or "").split()),
        "system": " ".join(str(raw.get("system") or "Other").split()),
        "kind": kind if kind in KINDS else "",
        "priority": priority if priority in PRIORITIES else "P2",
        "who": who if who in WHO else "",
        "status": status,
        "due": day(raw.get("due")),
        "remind": day(raw.get("remind")),
        "why": " ".join(str(raw.get("why") or "").split()),
        "source": " ".join(str(raw.get("source") or "").split()),
    }


def new_row(item: dict) -> dict:
    """Properties for a new row, from a normalise()d item."""
    props = {
        P_ITEM: {"title": rich_text(item["item"])},
        P_SYSTEM: select_prop(item["system"]),
        P_PRIORITY: select_prop(item["priority"]),
        P_STATUS: select_prop(item["status"]),
    }
    if item.get("kind"):
        props[P_KIND] = select_prop(item["kind"])
    if item.get("who"):
        props[P_WHO] = select_prop(item["who"])
    if item.get("due"):
        props[P_DUE] = date_prop(item["due"])
    if item.get("remind"):
        props[P_REMIND] = date_prop(item["remind"])
    if item.get("why"):
        props[P_WHY] = text_prop(item["why"])
    if item.get("source"):
        props[P_SOURCE] = text_prop(item["source"])
    return props


def same(a: str, b: str) -> bool:
    return " ".join(a.lower().split()) == " ".join(b.lower().split())


def read_all(notion, db_id: str) -> list[Item]:
    return [it for it in map(parse_item, notion.query_database(db_id)) if it.item]
