"""
Minimal Notion REST client for the mission board (plain requests, no SDK).

The token comes from NOTION_TOKEN in the workspace .env. It is read with
dotenv_values() rather than load_dotenv(), so nothing from .env leaks into
os.environ and from there into the Claude sessions the runner starts
(an ANTHROPIC_API_KEY there would switch them from the Pro plan to API billing).
"""

import os
import re
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent.parent
API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
VIEWS_VERSION = "2026-03-11"  # the views endpoint only exists from this version on
TEXT_LIMIT = 2000  # Notion's max characters per rich-text object


class NotionError(RuntimeError):
    pass


def load_token() -> str:
    token = dotenv_values(ROOT / ".env").get("NOTION_TOKEN") or os.environ.get("NOTION_TOKEN")
    if not token:
        raise NotionError(
            "NOTION_TOKEN is not set in .env. Create an internal integration at "
            "https://www.notion.so/profile/integrations and add its secret to .env "
            "as NOTION_TOKEN=..."
        )
    return token.strip()


def page_id_from(url_or_id: str) -> str:
    """Accepts a Notion URL or a bare id (with or without dashes); returns the dashed id."""
    candidates = re.findall(r"[0-9a-fA-F]{32}|[0-9a-fA-F-]{36}", url_or_id.split("?")[0])
    if not candidates:
        raise NotionError(f"Couldn't find a Notion page id in: {url_or_id}")
    raw = candidates[-1].replace("-", "").lower()
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


class Notion:
    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token or load_token()}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        })

    def _call(self, method: str, path: str, body: dict | None = None, params: dict | None = None,
              version: str | None = None) -> dict:
        headers = {"Notion-Version": version} if version else None
        for attempt in range(6):
            try:
                r = self.session.request(method, API + path, json=body, params=params, timeout=60,
                                         headers=headers)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt == 5:
                    raise NotionError(f"Can't reach Notion ({exc.__class__.__name__})") from exc
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            if r.status_code >= 400:
                try:
                    info = r.json()
                    msg = f"{info.get('code')}: {info.get('message')}"
                except ValueError:
                    msg = r.text[:300]
                raise NotionError(f"{method} {path} -> {r.status_code} {msg}")
            return r.json()
        raise NotionError(f"{method} {path} kept failing (rate limit or Notion outage)")

    def _paginate(self, method: str, path: str, body: dict | None = None) -> list[dict]:
        results, cursor = [], None
        while True:
            if method == "GET":
                params = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
                data = self._call("GET", path, params=params)
            else:
                data = self._call("POST", path, {**(body or {}), "page_size": 100,
                                                 **({"start_cursor": cursor} if cursor else {})})
            results += data.get("results", [])
            if not data.get("has_more"):
                return results
            cursor = data.get("next_cursor")

    # --- endpoints -------------------------------------------------------

    def me(self) -> dict:
        return self._call("GET", "/users/me")

    def get_page(self, page_id: str) -> dict:
        return self._call("GET", f"/pages/{page_id}")

    def get_database(self, db_id: str) -> dict:
        return self._call("GET", f"/databases/{db_id}")

    def create_database(self, body: dict) -> dict:
        return self._call("POST", "/databases", body)

    def update_database(self, db_id: str, body: dict) -> dict:
        return self._call("PATCH", f"/databases/{db_id}", body)

    def query_database(self, db_id: str, filter: dict | None = None, sorts: list | None = None) -> list[dict]:
        body = {}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        return self._paginate("POST", f"/databases/{db_id}/query", body)

    def create_page(self, body: dict) -> dict:
        return self._call("POST", "/pages", body)

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self._call("PATCH", f"/pages/{page_id}", {"properties": properties})

    def children(self, block_id: str) -> list[dict]:
        return self._paginate("GET", f"/blocks/{block_id}/children")

    def update_block(self, block_id: str, body: dict) -> dict:
        return self._call("PATCH", f"/blocks/{block_id}", body)

    def append(self, block_id: str, blocks: list[dict], after: str | None = None) -> list[dict]:
        """Appends blocks (at the end, or right after block `after`); returns the created blocks."""
        created = []
        for i in range(0, len(blocks), 100):
            body = {"children": blocks[i:i + 100], **({"after": after} if after else {})}
            created += self._call("PATCH", f"/blocks/{block_id}/children", body).get("results", [])
            if after and created:
                after = created[-1]["id"]
        return created

    def data_source_id(self, db_id: str) -> str:
        db = self._call("GET", f"/databases/{db_id}", version=VIEWS_VERSION)
        return db["data_sources"][0]["id"]

    def create_view(self, body: dict) -> dict:
        return self._call("POST", "/views", body, version=VIEWS_VERSION)


# --- rich text and blocks ------------------------------------------------

def plain(rich: list[dict]) -> str:
    return "".join(part.get("plain_text", "") for part in rich or [])


def _inline(text: str) -> list[dict]:
    """Turns **bold** and `code` into Notion annotations; everything else stays plain."""
    parts = []
    for token in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not token:
            continue
        bold = token.startswith("**") and token.endswith("**") and len(token) > 4
        code = token.startswith("`") and token.endswith("`") and len(token) > 2
        content = token[2:-2] if bold else token[1:-1] if code else token
        for i in range(0, len(content), TEXT_LIMIT):
            parts.append({"type": "text", "text": {"content": content[i:i + TEXT_LIMIT]},
                          "annotations": {"bold": bold, "code": code}})
    return parts


def rich_text(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text[i:i + TEXT_LIMIT]}}
            for i in range(0, len(text), TEXT_LIMIT)] or []


def block(kind: str, text: str = "", **extra) -> dict:
    if kind == "divider":
        return {"object": "block", "type": "divider", "divider": {}}
    return {"object": "block", "type": kind, kind: {"rich_text": _inline(text), **extra}}


def markdown_to_blocks(md: str) -> list[dict]:
    """Small line-based Markdown converter, enough for Claude's reports."""
    blocks, code_lines, in_code, lang = [], [], False, "plain text"
    for line in md.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                code = "\n".join(code_lines)
                blocks.append({"object": "block", "type": "code",
                               "code": {"rich_text": rich_text(code), "language": lang}})
                code_lines, in_code = [], False
            else:
                in_code, lang = True, "plain text"
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not stripped:
            continue
        if stripped.startswith("### "):
            blocks.append(block("heading_3", stripped[4:]))
        elif stripped.startswith("## ") or stripped.startswith("# "):
            blocks.append(block("heading_3", stripped.lstrip("#").strip()))
        elif re.match(r"^[-*] \[[ xX]\] ", stripped):
            blocks.append(block("to_do", stripped[6:], checked=stripped[3] in "xX"))
        elif stripped.startswith(("- ", "* ")):
            blocks.append(block("bulleted_list_item", stripped[2:]))
        elif re.match(r"^\d+[.)] ", stripped):
            blocks.append(block("numbered_list_item", re.sub(r"^\d+[.)] ", "", stripped)))
        elif stripped.startswith("> "):
            blocks.append(block("quote", stripped[2:]))
        elif stripped in ("---", "***"):
            blocks.append(block("divider"))
        else:
            blocks.append(block("paragraph", stripped))
    if in_code and code_lines:
        blocks.append({"object": "block", "type": "code",
                       "code": {"rich_text": rich_text("\n".join(code_lines)), "language": "plain text"}})
    return blocks
