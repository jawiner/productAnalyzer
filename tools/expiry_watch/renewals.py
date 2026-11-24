"""
The Renewals table in Notion: column names, schema, reading a row, local config.
"""

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
# Reuse the Notion client of the missions tool. Appended (not inserted first), so this
# folder's own modules win over same-named ones there.
sys.path.append(str(HERE.parent / "notion_missions"))
from notion_api import Notion, NotionError, block, page_id_from, plain, rich_text  # noqa: E402,F401

import rules  # noqa: E402

CONFIG_PATH = HERE / "board.json"
MISSIONS_CONFIG = HERE.parent / "notion_missions" / "board.json"
STATE_DIR = ROOT / ".tmp" / "expiry_watch"

P_NAME = "Name"
P_EXPIRES = "Expires"
P_DAYS = "Days left"
P_TYPE = "Type"
P_REPEATS = "Repeats"
P_AUTO = "Renews by itself"
P_COST = "Cost"
P_LINK = "Where to renew"
P_WARN = "Warn days before"
P_NOTES = "Notes"
P_PAUSED = "Paused"
P_STATUS = "Status"
P_ALERTED = "Last alert"
P_KEY = "Auto key"

TYPE_COLORS = {
    rules.T_SUBSCRIPTION: "blue", rules.T_DOMAIN: "green", rules.T_SSL: "yellow",
    rules.T_TOKEN: "purple", rules.T_LICENCE: "orange", rules.T_MEMBERSHIP: "pink",
    rules.T_OTHER: "gray",
}
# today(), not now(): now() carries the time of day and makes the count one short.
DAYS_FORMULA = 'dateBetween(prop("Expires"), today(), "days")'


def database_schema() -> dict:
    return {
        P_NAME: {"title": {}},
        P_EXPIRES: {"date": {}},
        P_TYPE: {"select": {"options": [{"name": t, "color": TYPE_COLORS[t]} for t in rules.TYPES]}},
        P_STATUS: {"rich_text": {}},
        P_REPEATS: {"select": {"options": [{"name": r} for r in rules.REPEATS]}},
        P_AUTO: {"checkbox": {}},
        P_COST: {"rich_text": {}},
        P_LINK: {"url": {}},
        P_NOTES: {"rich_text": {}},
        P_WARN: {"rich_text": {}},
        P_PAUSED: {"checkbox": {}},
        P_ALERTED: {"rich_text": {}},
        P_KEY: {"rich_text": {}},
    }


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise NotionError("The Renewals table isn't set up yet. Run: "
                          "python tools/expiry_watch/setup_board.py")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class Item:
    page_id: str | None
    name: str
    type: str = ""
    expires: date | None = None
    repeats: str = ""
    auto_renew: bool = False
    cost: str = ""
    link: str = ""
    notes: str = ""
    warn_text: str = ""
    paused: bool = False
    status: str = ""
    alerted: str = ""
    key: str = ""
    # Filled in by this run's automatic checks, never stored as such:
    problem: str | None = None
    note: str | None = None
    healthy: bool = False


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
        name=plain((p.get(P_NAME) or {}).get("title")).strip(),
        type=_select(p.get(P_TYPE)),
        expires=_date(p.get(P_EXPIRES)),
        repeats=_select(p.get(P_REPEATS)),
        auto_renew=bool((p.get(P_AUTO) or {}).get("checkbox")),
        cost=_text(p.get(P_COST)),
        link=(p.get(P_LINK) or {}).get("url") or "",
        notes=_text(p.get(P_NOTES)),
        warn_text=_text(p.get(P_WARN)),
        paused=bool((p.get(P_PAUSED) or {}).get("checkbox")),
        status=_text(p.get(P_STATUS)),
        alerted=_text(p.get(P_ALERTED)),
        key=_text(p.get(P_KEY)),
    )


def date_prop(d: date | None) -> dict:
    return {"date": {"start": d.isoformat()} if d else None}


def text_prop(text: str) -> dict:
    return {"rich_text": rich_text(text)}


def new_row(name: str, item_type: str, *, key: str = "", expires: date | None = None,
            paused: bool = False, notes: str = "", repeats: str = "", auto: bool = False,
            cost: str = "") -> dict:
    """Properties for a new row."""
    props = {
        P_NAME: {"title": rich_text(name)},
        P_TYPE: {"select": {"name": item_type}},
    }
    if key:
        props[P_KEY] = text_prop(key)
    if expires:
        props[P_EXPIRES] = date_prop(expires)
    if paused:
        props[P_PAUSED] = {"checkbox": True}
    if notes:
        props[P_NOTES] = text_prop(notes)
    if repeats:
        props[P_REPEATS] = {"select": {"name": repeats}}
    if auto:
        props[P_AUTO] = {"checkbox": True}
    if cost:
        props[P_COST] = text_prop(cost)
    return props
