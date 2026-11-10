"""
Live view of the missions board in Notion:
  - a "Live status" box above the board: what's being worked on now, what's waiting,
    what's finished, updated as the runner goes,
  - "Waiting · #n in line" on missions that haven't started,
  - on the running mission: how long it has been going and what Claude is doing right
    now, read from Claude Code's own session transcript.

The runner calls refresh() at the start, every 45 s while a mission runs, and at the end.
`python tools/notion_missions/run_missions.py --status` does one refresh by hand.
"""

import datetime
import json
import threading
import time
from pathlib import Path

from board import (DONE, DRAFT, FAILED, NEEDS_INFO, NEEDS_REVIEW, P_LAST_RUN, P_MISSION, P_RESULT,
                   P_STATUS, READY, RUNNING, is_trusted, prop_text, queue_order, save_config, short_id)
from notion_api import Notion, NotionError, rich_text

PROJECTS_DIR = Path.home() / ".claude" / "projects"  # Claude Code keeps session transcripts here
QUEUE_PREFIX = "Waiting · #"
WORKING_PREFIX = "Working · "
KEEP_NOTES = ("Paused", "Waiting: Claude usage")  # runner notes worth keeping next to the place in line


# --- what is Claude doing right now --------------------------------------------------

def describe_tool(name: str, inp: dict) -> str:
    file = Path(str(inp.get("file_path") or inp.get("notebook_path") or "")).name
    if name in ("Bash", "PowerShell"):
        if inp.get("description"):
            return str(inp["description"])[:90]
        # program name only: a full command line can carry a token (FOO=secret cmd ...)
        program = next((w for w in str(inp.get("command", "")).split() if "=" not in w), "")
        return f"Running {Path(program).name[:30]}" if program else "Running a command"
    if name == "Read":
        return f"Reading {file}"
    if name in ("Edit", "MultiEdit", "NotebookEdit"):
        return f"Editing {file}"
    if name == "Write":
        return f"Writing {file}"
    if name in ("Grep", "Glob"):
        return "Searching the code"
    if name in ("WebFetch", "WebSearch"):
        return "Looking something up online"
    if name in ("Agent", "Task"):
        return "Working with a helper agent"
    if name == "Skill":
        return f"Using the {inp.get('skill', '')} skill"
    return name


def _todo_step(inp: dict) -> str:
    todos = inp.get("todos") or []
    for i, todo in enumerate(todos, 1):
        if todo.get("status") == "in_progress":
            return f"Step {i}/{len(todos)}: {todo.get('activeForm') or todo.get('content', '')}"[:110]
    if todos and all(t.get("status") == "completed" for t in todos):
        return "Wrapping up"
    return ""


def find_transcript(short: str, since: float) -> Path | None:
    """Newest session transcript of a mission's work folder (worktree or scratch), touched since `since`."""
    files = [f for d in PROJECTS_DIR.glob(f"*-{short}*") if d.is_dir()
             for f in d.glob("*.jsonl") if f.stat().st_mtime >= since - 60]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def current_activity(short: str, since: float) -> str:
    path = find_transcript(short, since)
    if not path:
        return ""
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 3_000_000))
        lines = f.read().decode("utf-8", "replace").splitlines()[1:]  # the first line may be cut
    step = action = ""
    for line in reversed(lines):
        if step and action:
            break
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") != "assistant":
            continue
        for item in reversed(event.get("message", {}).get("content") or []):
            if item.get("type") != "tool_use":
                continue
            if item.get("name") == "TodoWrite":
                step = step or _todo_step(item.get("input") or {})
            elif not action:
                action = describe_tool(item.get("name", ""), item.get("input") or {})
    return " · ".join(x for x in (step, action) if x)


# --- writing it to Notion -----------------------------------------------------------------

def queue_text(pos: int, current: str) -> str:
    note = current
    if current.startswith(QUEUE_PREFIX):
        parts = current.split(" · ", 2)
        note = parts[2] if len(parts) == 3 else ""
    keep = note if note.startswith(KEEP_NOTES) else ""
    return f"{QUEUE_PREFIX}{pos} in line" + (f" · {keep}" if keep else "")


def _set_result(notion: Notion, page: dict, text: str) -> None:
    if prop_text(page, P_RESULT) != text:
        notion.update_page(page["id"], {P_RESULT: {"rich_text": rich_text(text[:1900])}})


def _started(page: dict) -> float | None:
    start = ((page["properties"].get(P_LAST_RUN) or {}).get("date") or {}).get("start")
    return datetime.datetime.fromisoformat(start).timestamp() if start else None


def summary_text(by_status: dict, now_lines: list[str], waiting: int) -> str:
    count = lambda s: len(by_status.get(s, []))
    lines = now_lines or ["💤 Not working on anything right now."]
    lines.append(f"⏳ Not started: {waiting} in line" + (f" · 📝 {count(DRAFT)} draft" if count(DRAFT) else ""))
    finished = f"✅ Finished: {count(NEEDS_REVIEW)} to check · {count(DONE)} done"
    lines.append(finished + (f" · ⚠️ {count(FAILED)} failed" if count(FAILED) else ""))
    if count(NEEDS_INFO):
        lines.append(f"❓ Waiting for your answer: {count(NEEDS_INFO)}")
    lines.append(f"Updated {datetime.datetime.now():%H:%M} · Claude checks for missions every hour")
    return "\n".join(lines)


def update_summary(notion: Notion, cfg: dict, text: str) -> None:
    """Rewrites the Live status box; creates it right above the board if it's missing or was deleted."""
    content = {"rich_text": rich_text(text), "icon": {"type": "emoji", "emoji": "📡"}, "color": "blue_background"}
    if cfg.get("status_block_id"):
        try:
            notion.update_block(cfg["status_block_id"], {"callout": content})
            return
        except NotionError:
            pass  # deleted or archived: make a new one
    children = notion.children(cfg["parent_page_id"])
    board_at = next((i for i, b in enumerate(children) if b["type"] == "child_database"), None)
    after = children[board_at - 1]["id"] if board_at else None
    created = notion.append(cfg["parent_page_id"], [{"object": "block", "type": "callout", "callout": content}], after)
    cfg["status_block_id"] = created[0]["id"]
    save_config(cfg)


def refresh(notion: Notion, cfg: dict, running: dict[str, float] | None = None) -> None:
    """One update of the live view. `running` maps the page id this process is running to its start time."""
    rows = notion.query_database(cfg["database_id"])
    by_status: dict[str, list[dict]] = {}
    for page in rows:
        by_status.setdefault(prop_text(page, P_STATUS), []).append(page)

    # Waiting missions get their place in line. Never write to a card someone else edited
    # last: our write would make us the last editor and hide their edit from the safety check.
    # (Such a card won't run either, so it doesn't take a place in line.)
    line = [p for p in queue_order(by_status.get(READY, [])) if is_trusted(p, cfg)]
    for pos, page in enumerate(line, 1):
        _set_result(notion, page, queue_text(pos, prop_text(page, P_RESULT)))

    now_lines = []
    for page in by_status.get(RUNNING, []):
        started = (running or {}).get(page["id"]) or _started(page)
        minutes = f"{int((time.time() - started) // 60)} min" if started else ""
        activity = current_activity(short_id(page["id"]), started or 0)
        live = " · ".join(x for x in (minutes, activity) if x)
        if page["id"] not in (running or {}):
            page = notion.get_page(page["id"])  # another process runs it: make sure it's still running
            if prop_text(page, P_STATUS) != RUNNING:
                continue
        _set_result(notion, page, WORKING_PREFIX + (live or "starting"))
        now_lines.append(f"🔄 Working on: {prop_text(page, P_MISSION)}" + (f" · {live}" if live else ""))

    # waiting = cards in line + new rows not picked up yet (named ones; an empty row isn't a mission)
    new_rows = [p for p in by_status.get("", []) if prop_text(p, P_MISSION)]
    update_summary(notion, cfg, summary_text(by_status, now_lines, len(line) + len(new_rows)))


class Ticker:
    """Calls refresh every `every` seconds in the background while a mission runs."""

    def __init__(self, fn, every: float = 45, log=None):
        self.fn, self.every, self.log = fn, every, log
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        warned = False
        while not self.stop_event.wait(self.every):
            try:
                self.fn()
            except Exception as exc:  # live updates must never break a mission
                if self.log and not warned:
                    self.log.warning("  live update failed (%s), the mission carries on", exc)
                    warned = True

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop_event.set()
        self.thread.join(timeout=120)
