"""
Read-only Gmail search over IMAP, using Gmail's own search syntax (X-GM-RAW).

The mailbox is opened read-only and bodies are fetched with BODY.PEEK, so nothing is
marked read, moved or changed. The password is never put in an error message.
"""

from __future__ import annotations

import email
import html
import imaplib
import re
from dataclasses import dataclass
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime

HOST = "imap.gmail.com"
BODY_BYTES = 65536  # headers and the start of the body are enough for a preview
SNIPPET_CHARS = 300


class InboxError(RuntimeError):
    pass


@dataclass
class Mail:
    msgid: str  # Gmail's own message id (X-GM-MSGID), stable across folders
    thread: str
    sender: str
    subject: str
    when: str
    snippet: str

    @property
    def link(self) -> str:
        return f"https://mail.google.com/mail/u/0/#all/{int(self.thread):x}" if self.thread.isdigit() else ""


def search_args(query: str) -> tuple[list[str], bytes | None]:
    """IMAP arguments for a Gmail search. Non-ASCII queries go as a UTF-8 literal."""
    try:
        query.encode("ascii")
    except UnicodeEncodeError:
        return ["CHARSET", "UTF-8", "X-GM-RAW"], query.encode("utf-8")
    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    return ["X-GM-RAW", f'"{escaped}"'], None


def all_mail_folder(list_lines: list[bytes]) -> str:
    """The folder flagged \\All ("All Mail" in any language), else INBOX."""
    for raw in list_lines:
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        m = re.match(r'\((?P<flags>[^)]*)\) (?:"[^"]*"|NIL) (?P<name>.+)$', line)
        if m and "\\All" in m.group("flags").split():
            return m.group("name").strip()
    return "INBOX"


def _text(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:  # noqa: BLE001 - a broken header shouldn't stop the run
        return value


def snippet_of(msg: email.message.Message) -> str:
    plain, rich = None, None
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() != "text" or part.get("Content-Disposition", "").startswith("attachment"):
            continue
        try:
            body = part.get_payload(decode=True) or b""
            text = body.decode(part.get_content_charset() or "utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        if part.get_content_subtype() == "plain" and plain is None:
            plain = text
        elif part.get_content_subtype() == "html" and rich is None:
            rich = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
            rich = html.unescape(re.sub(r"(?s)<[^>]+>", " ", rich))
    text = re.sub(r"\s+", " ", plain if plain is not None else rich or "").strip()
    return text[:SNIPPET_CHARS] + ("…" if len(text) > SNIPPET_CHARS else "")


def parse_mail(meta: str, raw: bytes) -> Mail:
    msg = email.message_from_bytes(raw)
    msgid = re.search(r"X-GM-MSGID (\d+)", meta)
    thread = re.search(r"X-GM-THRID (\d+)", meta)
    name, address = parseaddr(_text(msg.get("From")))
    when = ""
    try:
        when = parsedate_to_datetime(msg.get("Date")).astimezone().strftime("%a %d %b, %H:%M")
    except Exception:  # noqa: BLE001
        when = msg.get("Date", "")
    return Mail(
        msgid=msgid.group(1) if msgid else "",
        thread=thread.group(1) if thread else "",
        sender=f"{name} <{address}>" if name and address else (address or name or "unknown sender"),
        subject=_text(msg.get("Subject")) or "(no subject)",
        when=when,
        snippet=snippet_of(msg),
    )


class GmailInbox:
    """with GmailInbox(address, password) as inbox: inbox.search(query) -> {msgid: uid}"""

    def __init__(self, address: str, password: str, connect=None):
        self.address = address
        self._password = password
        self._connect = connect or (lambda: imaplib.IMAP4_SSL(HOST, 993, timeout=60))
        self.conn = None

    def __enter__(self) -> "GmailInbox":
        try:
            self.conn = self._connect()
        except OSError as exc:
            raise InboxError(f"Can't reach Gmail ({type(exc).__name__})") from None
        try:
            self.conn.login(self.address, self._password)
        except imaplib.IMAP4.error:
            raise InboxError("Gmail refused the sign-in. The app password may have been removed; "
                             "make a new one in the Google account and put it in .env") from None
        typ, lines = self.conn.list()
        folder = all_mail_folder(lines or []) if typ == "OK" else "INBOX"
        typ, _ = self.conn.select(folder, readonly=True)
        if typ != "OK":
            raise InboxError("Couldn't open the mailbox")
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self.conn is not None:
                self.conn.logout()
        except Exception:  # noqa: BLE001
            pass

    def search(self, query: str) -> dict[str, str]:
        """Matching messages as {gmail msgid: imap uid}."""
        args, literal = search_args(query)
        if literal is not None:
            self.conn.literal = literal
        typ, data = self.conn.uid("SEARCH", *args)
        if typ != "OK":
            raise InboxError(f"Gmail didn't accept the search: {query}")
        uids = (data[0] or b"").split() if data else []
        if not uids:
            return {}
        typ, data = self.conn.uid("FETCH", b",".join(uids).decode(), "(X-GM-MSGID)")
        found = {}
        for item in data or []:
            line = (item[0] if isinstance(item, tuple) else item) or b""
            line = line.decode("utf-8", "replace") if isinstance(line, bytes) else str(line)
            uid, msgid = re.search(r"UID (\d+)", line), re.search(r"X-GM-MSGID (\d+)", line)
            if uid and msgid:
                found[msgid.group(1)] = uid.group(1)
        return found

    def fetch(self, uid: str) -> Mail:
        typ, data = self.conn.uid("FETCH", uid, f"(X-GM-MSGID X-GM-THRID BODY.PEEK[]<0.{BODY_BYTES}>)")
        for item in data or []:
            if isinstance(item, tuple) and len(item) >= 2:
                meta = item[0].decode("utf-8", "replace") if isinstance(item[0], bytes) else str(item[0])
                return parse_mail(meta, item[1])
        raise InboxError("Couldn't read a matching email")
