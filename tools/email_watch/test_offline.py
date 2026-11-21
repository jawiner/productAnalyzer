"""
Offline checks for Email Watch: a fake Gmail (IMAP) server and a fake Telegram, nothing real.

    python tools/email_watch/test_offline.py
"""

from __future__ import annotations

import imaplib
import sys
import tempfile
from datetime import date
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gmail_inbox  # noqa: E402
import watch  # noqa: E402
from gmail_inbox import GmailInbox, InboxError, Mail, all_mail_folder, search_args  # noqa: E402
from notify import TelegramError, pieces  # noqa: E402

PASSED = 0


def ok(cond, what):
    global PASSED
    if not cond:
        raise AssertionError(what)
    PASSED += 1


def raw_mail(sender, subject, body, html_body=None, date_hdr="Sat, 21 Nov 2026 10:05:00 +0000"):
    m = EmailMessage()
    m["From"], m["Subject"], m["Date"] = sender, subject, date_hdr
    m.set_content(body)
    if html_body:
        m.add_alternative(html_body, subtype="html")
    return m.as_bytes()


class FakeIMAP:
    """Speaks just enough IMAP: messages are (uid, msgid, thrid, raw, words that match)."""

    def __init__(self, messages, password="right", folder_lines=None):
        self.messages, self.password = messages, password
        self.folder_lines = folder_lines or [b'(\\HasNoChildren \\All) "/" "[Gmail]/All Mail"', b'(\\HasNoChildren) "/" "INBOX"']
        self.literal = None
        self.selected = None
        self.searches = []
        self.fetched = []

    def login(self, user, password):
        if password != self.password:
            raise imaplib.IMAP4.error("AUTHENTICATIONFAILED")

    def list(self):
        return "OK", self.folder_lines

    def select(self, folder, readonly=False):
        self.selected = (folder, readonly)
        return "OK", [b"3"]

    def uid(self, command, *args):
        if command == "SEARCH":
            if self.literal is not None:
                query, self.literal = self.literal.decode("utf-8"), None
            else:
                query = args[-1].strip('"')
            self.searches.append(query)
            words = query.split(")")[0].strip("(").lower()
            hits = [m for m in self.messages if any(w in words for w in m[4])]
            return "OK", [" ".join(str(m[0]) for m in hits).encode()]
        if command == "FETCH":
            uids, what = args
            out = []
            for m in self.messages:
                if str(m[0]) in uids.split(","):
                    if what == "(X-GM-MSGID)":
                        out.append(f"1 (X-GM-MSGID {m[1]} UID {m[0]})".encode())
                    else:
                        self.fetched.append(str(m[0]))
                        ok("BODY.PEEK" in what, "bodies are fetched with PEEK, so nothing is marked read")
                        out.append((f"1 (X-GM-THRID {m[2]} X-GM-MSGID {m[1]} UID {m[0]} BODY[]<0> {{{len(m[3])}}}".encode(), m[3]))
                        out.append(b")")
            return "OK", out
        raise AssertionError(command)

    def logout(self):
        pass


GARMIN = (11, "1001", "777", raw_mail("Garmin Developer Program <connect-developer@garmin.com>",
                                      "Your Garmin Connect Developer Program request", "Hello, your request has been approved."), {"garmin"})
SALE = (12, "1002", "778", raw_mail("Shop <deals@shop.example>", "Holiday sale", "50% off <b>"), {"sale"})


def items_with(*pairs):
    items = []
    for title, query in pairs:
        watch.add_item(items, title, query, date(2026, 11, 21), since="2026-11-21")
    return items


class Sent(list):
    def __call__(self, text):
        self.append(text)


def failing_send(text):
    raise TelegramError("Telegram refused (401): Unauthorized")


def inbox_for(server, password="right"):
    return lambda: GmailInbox("me@example.com", password, connect=lambda: server)


# ---------- gmail_inbox ----------

def test_inbox():
    ok(all_mail_folder([b'(\\HasNoChildren) "/" "INBOX"', b'(\\All \\HasNoChildren) "/" "[Gmail]/&BdsF3A- &BdQF0wXV-"']) == '"[Gmail]/&BdsF3A- &BdQF0wXV-"',
       "finds All Mail by its flag in any language")
    ok(all_mail_folder([b'(\\HasNoChildren) "/" "INBOX"']) == "INBOX", "falls back to INBOX")
    args, literal = search_args('subject:"approved" from:garmin.com')
    ok(args == ["X-GM-RAW", '"subject:\\"approved\\" from:garmin.com"'] and literal is None, "ASCII query is quoted and escaped")
    args, literal = search_args("גרמין")
    ok(args == ["CHARSET", "UTF-8", "X-GM-RAW"] and literal == "גרמין".encode(), "Hebrew query goes as a UTF-8 literal")

    server = FakeIMAP([GARMIN, SALE])
    with GmailInbox("me@example.com", "right", connect=lambda: server) as inbox:
        ok(server.selected == ('"[Gmail]/All Mail"', True), "All Mail is opened read-only")
        hits = inbox.search("(garmin) after:2026/11/20")
        ok(hits == {"1001": "11"}, f"search maps Gmail ids to uids: {hits}")
        mail = inbox.fetch("11")
    ok(mail.sender == "Garmin Developer Program <connect-developer@garmin.com>", mail.sender)
    ok(mail.subject == "Your Garmin Connect Developer Program request", mail.subject)
    ok(mail.snippet == "Hello, your request has been approved.", mail.snippet)
    ok(mail.link == f"https://mail.google.com/mail/u/0/#all/{777:x}", mail.link)

    try:
        with GmailInbox("me@example.com", "wrong-secret-xyz", connect=lambda: FakeIMAP([], password="right")):
            pass
        ok(False, "a wrong password must fail")
    except InboxError as exc:
        ok("wrong-secret-xyz" not in str(exc) and "refused" in str(exc), "sign-in error never shows the password")

    html_only = EmailMessage()
    html_only["From"], html_only["Subject"] = "a@b.c", "x"
    html_only.set_content("<html><style>p{}</style><p>Hi &amp; welcome</p><script>x()</script></html>", subtype="html")
    ok(gmail_inbox.snippet_of(html_only) == "Hi & welcome", "HTML-only mail gets a clean text preview")
    long = EmailMessage()
    long.set_content("word " * 200)
    ok(gmail_inbox.snippet_of(long).endswith("…") and len(gmail_inbox.snippet_of(long)) <= 301, "previews are cut at 300 characters")


# ---------- check ----------

def test_check():
    today = date(2026, 11, 23)  # a Monday; Sundays are tested at the end
    server = FakeIMAP([GARMIN, SALE])
    items = items_with(("Garmin developer program reply", "garmin developer"))
    state, sent = {}, Sent()
    code = watch.check(items, state, inbox_for(server), sent, today)
    ok(code == 0 and len(sent) == 1, "a new matching email sends one message")
    ok("Garmin developer program reply</b>: 1 new email" in sent[0] and "connect-developer@garmin.com" in sent[0]
       and "Your Garmin Connect Developer Program request" in sent[0], "the message names the item, sender and subject")
    ok("Holiday sale" not in sent[0], "emails that don't match aren't reported")
    ok(state["seen"][items[0]["id"]] == ["1001"] and state["last_ok"] == "2026-11-23", "the email is remembered")
    ok(server.searches[0] == "(garmin developer) after:2026/11/20", f"first search starts a day before 'since': {server.searches[0]}")

    sent2 = Sent()
    ok(watch.check(items, state, inbox_for(server), sent2, date(2026, 11, 24)) == 0 and sent2 == [], "the same email is never reported twice")
    ok(server.searches[-1] == "(garmin developer) after:2026/11/20", f"later searches start 2 days before the last good check: {server.searches[-1]}")

    # Telegram down: nothing is marked as seen, so the next run tries again.
    items = items_with(("Garmin", "garmin"))
    state = {}
    ok(watch.check(items, state, inbox_for(FakeIMAP([GARMIN])), failing_send, today) == 2, "Telegram failure exits 2")
    ok("seen" not in state and "last_ok" not in state, "nothing is marked seen when the message didn't go out")
    sent = Sent()
    ok(watch.check(items, state, inbox_for(FakeIMAP([GARMIN])), sent, today) == 0 and len(sent) == 1, "the next run sends it")

    # Gmail down: one alert a day.
    sent = Sent()
    state = {}
    bad = inbox_for(FakeIMAP([], password="right"), password="wrong")
    ok(watch.check(items, state, bad, sent, today) == 1 and len(sent) == 1 and "couldn't check Gmail" in sent[0], "Gmail problem alerts")
    ok(watch.check(items, state, bad, sent, today) == 1 and len(sent) == 1, "only one Gmail alert a day")
    ok(watch.check(items, state, bad, sent, date(2026, 11, 24)) == 1 and len(sent) == 2, "and again the next day")

    # Many matches: the newest five are shown, the rest counted.
    many = [(100 + n, str(5000 + n), "9", raw_mail("x@y.z", f"Order {n}", "ok"), {"order"}) for n in range(8)]
    sent = Sent()
    watch.check(items_with(("Orders", "order")), {}, inbox_for(FakeIMAP(many)), sent, today)
    ok("8 new emails" in sent[0] and "Order 7" in sent[0] and "Order 2" not in sent[0] and "…and 3 more" in sent[0], "caps at five per item")

    # HTML in subjects is escaped for Telegram.
    sneaky = (21, "2001", "5", raw_mail("a <a@b.c>", "Price <b>&</b> deals", "x"), {"price"})
    sent = Sent()
    watch.check(items_with(("Prices", "price")), {}, inbox_for(FakeIMAP([sneaky])), sent, today)
    ok("Price &lt;b&gt;&amp;&lt;/b&gt; deals" in sent[0], "subjects are HTML-escaped")

    # End dates.
    items = items_with(("Old thing", "garmin"))
    items[0]["until"] = "2026-11-22"
    sent, state = Sent(), {}
    server = FakeIMAP([GARMIN])
    watch.check(items, state, inbox_for(server), sent, today)
    ok(items[0]["status"] == "expired" and server.searches == [] and "Stopped watching <b>Old thing</b>" in sent[0], "items past their end date stop")

    # Quiet when nothing is new; dry runs change nothing.
    sent, state = Sent(), {}
    ok(watch.check(items_with(("Nothing", "nomatch")), state, inbox_for(FakeIMAP([GARMIN])), sent, today) == 0 and sent == [], "no message when nothing is new")
    out, state, items = [], {}, items_with(("Garmin", "garmin"))
    ok(watch.check(items, state, inbox_for(FakeIMAP([GARMIN])), failing_send, today, dry_run=True, out=out.append) == 0, "dry run never sends")
    ok("Garmin" in out[0] and state == {}, "dry run prints and changes nothing")

    # Sundays: the list.
    sunday = date(2026, 11, 22)
    sent, state = Sent(), {}
    watch.check(items_with(("Garmin", "nomatch"), ("Visa", "nomatch2")), state, inbox_for(FakeIMAP([])), sent, sunday)
    ok(len(sent) == 1 and "watching 2 things" in sent[0] and "• Visa (since 2026-11-21)" in sent[0], "Sunday message lists what's watched")
    watch.check(items_with(("Garmin", "nomatch")), state, inbox_for(FakeIMAP([])), sent, sunday)
    ok(len(sent) == 1, "only once that Sunday")


# ---------- list commands ----------

def test_commands():
    with tempfile.TemporaryDirectory() as tmp:
        watch.LIST_FILE, watch.STATE_FILE = Path(tmp) / "watchlist.json", Path(tmp) / "state.json"
        ok(watch.main(["add", "Garmin developer program reply", "--query", "garmin developer", "--since", "2026-11-21"]) == 0, "add works")
        ok(watch.main(["add", "Garmin developer program reply", "--query", "garmin api"]) == 0, "a second item with the same title works")
        items = watch.load(watch.LIST_FILE, {})["items"]
        ok([i["id"] for i in items] == ["garmin-developer-program-reply", "garmin-developer-program-reply-2"], "ids are unique")
        ok(watch.main(["done", "garmin-developer-program-reply-2"]) == 0, "done works")
        ok(watch.load(watch.LIST_FILE, {})["items"][1]["status"] == "done", "done stops the item")
        try:
            watch.main(["add", "Bad", "--query", "x", "--until", "next week"])
            ok(False, "bad dates must fail")
        except ValueError:
            ok(True, "bad dates are refused")
        watch.save(watch.STATE_FILE, {"last_ok": date.today().isoformat()})
        ok(watch.main(["--if-due"]) == 0, "--if-due skips when today's check succeeded (no Gmail call)")
    ok(len(pieces("a" * 3000 + "\n\n" + "b" * 3000)) == 2, "long Telegram messages split between blocks")


if __name__ == "__main__":
    test_inbox()
    test_check()
    test_commands()
    print(f"All {PASSED} checks passed.")
