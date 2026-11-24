"""
Offline test of the expiry watcher: fake Notion, fake lookups, fake Telegram.
Touches nothing real and sends nothing.

    python tools/expiry_watch/test_offline.py
"""

import sys
from datetime import date, timedelta

import checks
import rules
import telegram_send
import watch
from checks import Check
from renewals import (P_ALERTED, P_AUTO, P_EXPIRES, P_KEY, P_NAME, P_PAUSED, P_REPEATS, P_STATUS,
                      P_TYPE, P_WARN, new_row, plain, text_prop)

passed = failed = 0


def check(label: str, condition: bool, got=None) -> None:
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"FAIL  {label}" + (f"  (got {got!r})" if got is not None else ""))


class FakeNotion:
    def __init__(self):
        self.pages: dict[str, dict] = {}
        self.count = 0
        self.updates = 0

    def add(self, name, item_type, **kwargs) -> str:
        warn = kwargs.pop("warn", "")
        alerted = kwargs.pop("alerted", "")
        props = new_row(name, item_type, **kwargs)
        if warn:
            props[P_WARN] = text_prop(warn)
        if alerted:
            props[P_ALERTED] = text_prop(alerted)
        return self.create_page({"properties": props})["id"]

    def create_page(self, body):
        self.count += 1
        page_id = f"page-{self.count}"
        self.pages[page_id] = {"id": page_id, "properties": self._store(body["properties"])}
        return {"id": page_id}

    def update_page(self, page_id, props):
        self.updates += 1
        self.pages[page_id]["properties"].update(self._store(props))
        return {}

    def query_database(self, db_id):
        return list(self.pages.values())

    @staticmethod
    def _store(props):
        """Notion returns rich text with plain_text; the writer sends text.content."""
        out = {}
        for name, value in props.items():
            value = dict(value)
            for kind in ("rich_text", "title"):
                if kind in value:
                    value[kind] = [{"plain_text": part["text"]["content"]} for part in value[kind]]
            out[name] = value
        return out

    def prop(self, page_id, name):
        value = self.pages[page_id]["properties"].get(name, {})
        if not value:
            return ""
        if "rich_text" in value:
            return plain(value["rich_text"])
        if "date" in value:
            return (value["date"] or {}).get("start")
        return value


class World:
    """Everything outside the watcher, under the test's control."""

    def __init__(self):
        self.notion = FakeNotion()
        self.sent: list[str] = []
        self.domains: dict[str, tuple] = {}
        self.ssl: dict[str, Check] = {}
        self.tokens: list[Check] = []
        self.fail_send = False
        self.said: list[str] = []

    def send(self, text):
        if self.fail_send:
            raise telegram_send.TelegramError("Can't reach Telegram (ConnectionError)")
        self.sent.append(text)

    def run(self, today, dry_run=False):
        return watch.run(
            self.notion, {"database_id": "db"}, today, send=self.send,
            domain_lookup=lambda host: self.domains.get(host, (None, checks.NO_DATE_NOTE)),
            ssl_lookup=lambda host: self.ssl.get(host) or Check(f"ssl:{host}", f"{host} certificate",
                                                                 rules.T_SSL, checks.UNKNOWN, None, "n/a"),
            token_checks=lambda cfg: (list(self.tokens), []),
            dry_run=dry_run, say=self.said.append)


TODAY = date(2026, 11, 10)


def test_rules():
    w = rules.DEFAULT_WARN
    check("far away: no stage", rules.stage(45, w) is None)
    check("30 days", rules.stage(30, w) == "30")
    check("20 days is still the 30 stage", rules.stage(20, w) == "30")
    check("14 days", rules.stage(14, w) == "14")
    check("5 days is the 7 stage", rules.stage(5, w) == "7")
    check("today", rules.stage(0, w) == "0")
    check("1 day late", rules.stage(-1, w) == "late1")
    check("3 days late", rules.stage(-3, w) == "late3")
    check("5 days late: no new stage", rules.stage(-5, w) == "late3")
    check("10 days late: weekly", rules.stage(-10, w) == "late-week1")
    check("17 days late: next week", rules.stage(-17, w) == "late-week2")
    check("custom warn list", rules.parse_warn("60, 30 ,7") == [60, 30, 7])
    check("empty warn list", rules.parse_warn("") is None)
    check("words only", rules.parse_warn("soon") is None)
    check("monthly auto default", rules.default_warn(rules.T_SUBSCRIPTION, rules.R_MONTHLY, True) == [3, 1])
    check("add month clamps", rules.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28))
    check("roll monthly", rules.roll_forward(date(2026, 10, 31), rules.R_MONTHLY, TODAY) == date(2026, 11, 30))
    check("roll keeps the 31st", rules.roll_forward(date(2026, 10, 31), rules.R_MONTHLY, date(2026, 12, 5))
          == date(2026, 12, 31))
    check("roll yearly", rules.roll_forward(date(2024, 3, 1), rules.R_YEARLY, TODAY) == date(2027, 3, 1))
    check("no roll for future", rules.roll_forward(date(2027, 1, 1), rules.R_MONTHLY, TODAY) == date(2027, 1, 1))
    check("no roll on the day", rules.roll_forward(TODAY, rules.R_MONTHLY, TODAY) == TODAY)
    check("when: days", rules.when_text(5, False) == "Expires in 5 days")
    check("when: tomorrow auto", rules.when_text(1, True) == "Renews by itself tomorrow")
    check("when: ago", rules.when_text(-4, False) == "Expired 4 days ago")
    text = rules.format_digest([{"name": "A <b>", "type": "Other", "expires": TODAY, "days_left": 0,
                                 "auto": False, "problem": None, "cost": "", "link": "", "notes": ""}], TODAY)
    check("digest escapes names", "A &lt;b&gt;" in text, text)


def test_checks_parsing():
    check("host from url", checks.host_of("https://www.Mashtech.co.il/page") == "www.mashtech.co.il")
    check("not a host", checks.host_of("My domain") is None)
    check("registrable .co.il", checks.registrable("www.mashtech.co.il") == "mashtech.co.il")
    check("registrable .cloud", checks.registrable("app.castly.cloud") == "castly.cloud")
    check("shared host", checks.registrable("lifemaxing-bice.vercel.app") is None)
    check("iso date", checks.parse_date("2027-03-09T12:00:00Z") == date(2027, 3, 9))
    check("day-first date", checks.parse_date("10-09-2027") == date(2027, 9, 10))
    check("month name date", checks.parse_date("09-Mar-2027") == date(2027, 3, 9))
    check("garbage date", checks.parse_date("N/A") is None)
    check("whois .il", checks.parse_whois_expiry("domain: x.co.il\nvalidity:     10-09-2027\n") == date(2027, 9, 10))
    check("whois com", checks.parse_whois_expiry("   Registry Expiry Date: 2027-08-01T04:00:00Z\n")
          == date(2027, 8, 1))
    check("whois without date", checks.parse_whois_expiry("validity: N/A\n") is None)
    check("jwt without exp", checks.jwt_expiry("abc.def.ghi") is None)
    check("plain key is no jwt", checks.jwt_expiry("sk-123") is None)


def test_alert_once_per_stage():
    w = World()
    pid = w.notion.add("Figma", rules.T_SUBSCRIPTION, expires=TODAY + timedelta(days=7))
    far = w.notion.add("Far away", rules.T_LICENCE, expires=TODAY + timedelta(days=200))
    w.run(TODAY)
    check("alert at 7 days", len(w.sent) == 1 and "Figma" in w.sent[0] and "in 7 days" in w.sent[0], w.sent)
    check("far item not mentioned", "Far away" not in w.sent[0])
    check("marker stored", w.notion.prop(pid, P_ALERTED) == f"{(TODAY + timedelta(days=7)).isoformat()}|7")
    check("status soon", w.notion.prop(pid, P_STATUS).startswith("🟡"), w.notion.prop(pid, P_STATUS))
    check("status ok", w.notion.prop(far, P_STATUS) == "🟢 OK", w.notion.prop(far, P_STATUS))
    w.run(TODAY)
    check("same day: no repeat", len(w.sent) == 1)
    w.run(TODAY + timedelta(days=2))
    check("5 days left: same stage, quiet", len(w.sent) == 1)
    w.run(TODAY + timedelta(days=4))
    check("3 days left: new alert", len(w.sent) == 2 and "in 3 days" in w.sent[1], w.sent)
    check("status red", w.notion.prop(pid, P_STATUS).startswith("🔴"))
    w.run(TODAY + timedelta(days=7))
    check("on the day", len(w.sent) == 3 and "Expires today" in w.sent[2], w.sent)
    w.run(TODAY + timedelta(days=8))
    check("day after", len(w.sent) == 4 and "Expired yesterday" in w.sent[3], w.sent)
    w.run(TODAY + timedelta(days=12))
    check("5 days late after a gap: one alert", len(w.sent) == 5 and "Expired 5 days ago" in w.sent[4], w.sent)
    w.run(TODAY + timedelta(days=13))
    check("6 days late: quiet", len(w.sent) == 5)
    w.run(TODAY + timedelta(days=17))
    check("10 days late: weekly reminder", len(w.sent) == 6, w.sent)


def test_renewed_item_starts_over():
    w = World()
    pid = w.notion.add("Licence", rules.T_LICENCE, expires=TODAY + timedelta(days=3))
    w.run(TODAY)
    check("alerted", len(w.sent) == 1)
    w.notion.update_page(pid, {P_EXPIRES: {"date": {"start": (TODAY + timedelta(days=368)).isoformat()}}})
    w.run(TODAY + timedelta(days=1))
    check("renewed: quiet", len(w.sent) == 1)
    check("renewed: marker cleared", w.notion.prop(pid, P_ALERTED) == "", w.notion.prop(pid, P_ALERTED))
    check("renewed: status ok", w.notion.prop(pid, P_STATUS) == "🟢 OK")


def test_pc_was_off():
    w = World()
    w.notion.add("Membership", rules.T_MEMBERSHIP, expires=TODAY + timedelta(days=40))
    w.run(TODAY)
    check("40 days: quiet", not w.sent)
    w.run(TODAY + timedelta(days=38))  # first run after a long break, 2 days left
    check("one alert with the real days", len(w.sent) == 1 and "in 2 days" in w.sent[0], w.sent)


def test_failed_send_retries():
    w = World()
    pid = w.notion.add("Thing", rules.T_OTHER, expires=TODAY + timedelta(days=1))
    w.fail_send = True
    try:
        w.run(TODAY)
        check("failed send raises", False)
    except telegram_send.TelegramError:
        check("failed send raises", True)
    check("no marker after a failed send", w.notion.prop(pid, P_ALERTED) == "", w.notion.prop(pid, P_ALERTED))
    w.fail_send = False
    w.run(TODAY)
    check("sent on the next run", len(w.sent) == 1 and "tomorrow" in w.sent[0], w.sent)


def test_auto_renew():
    w = World()
    pid = w.notion.add("Claude", rules.T_SUBSCRIPTION, expires=TODAY + timedelta(days=3),
                       repeats=rules.R_MONTHLY, auto=True, cost="$100 / month")
    w.run(TODAY - timedelta(days=10))
    check("auto monthly: quiet 13 days ahead", not w.sent)
    w.run(TODAY)
    check("auto monthly: heads-up at 3 days",
          len(w.sent) == 1 and "Renews by itself in 3 days" in w.sent[0] and "$100" in w.sent[0], w.sent)
    w.run(TODAY + timedelta(days=3))
    check("auto: last heads-up on the day when the PC missed the day before",
          len(w.sent) == 2 and "Renews by itself today" in w.sent[1], w.sent)
    before = len(w.sent)
    w.run(TODAY + timedelta(days=5))
    check("auto: date moved a month on", w.notion.prop(pid, P_EXPIRES) == "2026-12-13",
          w.notion.prop(pid, P_EXPIRES))
    check("auto: no 'expired' alert", len(w.sent) == before, w.sent)


def test_paused_and_custom_warn():
    w = World()
    w.notion.add("Paused", rules.T_OTHER, expires=TODAY, paused=True)
    pid = w.notion.add("Passport", rules.T_OTHER, expires=TODAY + timedelta(days=85), warn="90, 30")
    w.notion.add("", rules.T_OTHER)  # an empty row someone left behind
    summary = w.run(TODAY)
    check("paused is silent", len(w.sent) == 1 and "Paused" not in w.sent[0], w.sent)
    check("custom 90-day warning", "Passport" in w.sent[0] and "in 85 days" in w.sent[0])
    check("custom marker", w.notion.prop(pid, P_ALERTED).endswith("|90"))
    check("empty row ignored", summary["items"] == 2, summary["items"])


def test_no_date_row():
    w = World()
    pid = w.notion.add("Apple Developer", rules.T_MEMBERSHIP)
    summary = w.run(TODAY)
    check("no date: silent", not w.sent)
    check("no date: counted", summary["no_date"] == 1)
    check("no date: status", w.notion.prop(pid, P_STATUS) == "⚪ No date yet")


def test_domains_and_certificates():
    w = World()
    pid = w.notion.add("https://www.mashtech.co.il/", rules.T_DOMAIN)
    shared = w.notion.add("lifemaxing-bice.vercel.app", rules.T_DOMAIN)
    w.domains["www.mashtech.co.il"] = (TODAY + timedelta(days=10), "")
    w.domains["lifemaxing-bice.vercel.app"] = (None, checks.SHARED_NOTE)
    w.ssl["www.mashtech.co.il"] = Check("ssl:www.mashtech.co.il", "www.mashtech.co.il certificate",
                                         rules.T_SSL, checks.OK, TODAY + timedelta(days=60), "auto")
    summary = w.run(TODAY)
    check("domain date filled in", w.notion.prop(pid, P_EXPIRES) == (TODAY + timedelta(days=10)).isoformat())
    check("domain alert", len(w.sent) == 1 and "in 10 days" in w.sent[0], w.sent)
    check("certificate rows added", len(summary["created"]) == 2, summary["created"])
    cert = next(p for p, page in w.notion.pages.items()
                if w.notion.prop(p, P_KEY) == "ssl:www.mashtech.co.il")
    check("certificate date", w.notion.prop(cert, P_EXPIRES) == (TODAY + timedelta(days=60)).isoformat())
    check("certificate at 60 days: quiet", "certificate" not in w.sent[0])
    check("shared host note", checks.SHARED_NOTE in w.notion.prop(shared, P_STATUS), w.notion.prop(shared, P_STATUS))
    check("shared host isn't a no-date row", summary["no_date"] == 0, summary["no_date"])
    pages = len(w.notion.pages)
    w.run(TODAY)
    check("no duplicate rows on the next run", len(w.notion.pages) == pages)

    # The certificate was not renewed by the host.
    w.ssl["www.mashtech.co.il"].expires = TODAY + timedelta(days=9)
    w.run(TODAY + timedelta(days=1))
    check("certificate alert", len(w.sent) == 2 and "certificate" in w.sent[1], w.sent)

    # Registry unreachable: the date already there stays.
    w.domains["www.mashtech.co.il"] = (None, checks.NO_DATE_NOTE)
    w.run(TODAY + timedelta(days=1))
    check("lookup failure keeps the date", w.notion.prop(pid, P_EXPIRES) == (TODAY + timedelta(days=10)).isoformat())

    # The domain row is deleted: its certificate row is left alone, marked, and silent.
    del w.notion.pages[pid]
    sent = len(w.sent)
    w.run(TODAY + timedelta(days=6))
    check("orphan row marked", w.notion.prop(cert, P_STATUS) == watch.ORPHAN_STATUS, w.notion.prop(cert, P_STATUS))
    check("orphan row silent", len(w.sent) == sent, w.sent)
    check("orphan row not deleted", cert in w.notion.pages)


def test_keys():
    w = World()
    good = Check("token:wat:A_KEY", "A_KEY (wat)", rules.T_TOKEN, checks.OK, None, "Key works")
    w.tokens = [good]
    w.run(TODAY)
    pid = next(iter(w.notion.pages))
    check("working key: quiet", not w.sent)
    check("working key: status", w.notion.prop(pid, P_STATUS) == "🟢 Key works", w.notion.prop(pid, P_STATUS))

    w.tokens = [Check("token:wat:A_KEY", "A_KEY (wat)", rules.T_TOKEN, checks.PROBLEM, None,
                      "The service rejected this key (answer 401). It expired or was revoked")]
    w.run(TODAY + timedelta(days=1))
    check("rejected key: alert", len(w.sent) == 1 and "rejected" in w.sent[0] and "A_KEY" in w.sent[0], w.sent)
    check("rejected key: status", w.notion.prop(pid, P_STATUS).startswith("🔴"))
    w.run(TODAY + timedelta(days=2))
    check("still rejected, same week: quiet", len(w.sent) == 1)
    w.run(TODAY + timedelta(days=8))
    check("still rejected a week later: reminder", len(w.sent) == 2)

    w.tokens = [Check("token:wat:A_KEY", "A_KEY (wat)", rules.T_TOKEN, checks.UNKNOWN, None,
                      "Couldn't reach the service today (ConnectionError)")]
    summary = w.run(TODAY + timedelta(days=9))
    check("no internet is not an alert", len(w.sent) == 2 and summary["unknown"] == 1)

    w.tokens = [good]
    w.run(TODAY + timedelta(days=10))
    check("fixed key: marker cleared", w.notion.prop(pid, P_ALERTED) == "")
    check("fixed key: status", w.notion.prop(pid, P_STATUS) == "🟢 Key works")
    check("one row for the key throughout", len(w.notion.pages) == 1)

    # A key with a known end date warns like anything else.
    w.tokens = [Check("token:wat:JWT", "JWT (wat)", rules.T_TOKEN, checks.OK, TODAY + timedelta(days=24),
                      "End date read from the key itself"), good]
    w.run(TODAY + timedelta(days=10))
    check("key with end date: alert", len(w.sent) == 3 and "JWT" in w.sent[2] and "in 14 days" in w.sent[2], w.sent)


def test_dry_run_changes_nothing():
    w = World()
    pid = w.notion.add("Thing", rules.T_OTHER, expires=TODAY + timedelta(days=1))
    w.tokens = [Check("token:wat:A_KEY", "A_KEY (wat)", rules.T_TOKEN, checks.OK, None, "Key works")]
    w.run(TODAY, dry_run=True)
    check("dry run: nothing sent", not w.sent)
    check("dry run: no rows added", len(w.notion.pages) == 1)
    check("dry run: no updates", w.notion.updates == 0 and w.notion.prop(pid, P_STATUS) == "")
    check("dry run: shows the message", any("Thing" in line for line in w.said), w.said)


def test_message_split():
    long_text = "\n\n".join(f"item {i} " + "x" * 300 for i in range(40))
    pieces = telegram_send._pieces(long_text)
    check("long message split", len(pieces) > 1 and all(len(p) <= telegram_send.LIMIT for p in pieces))
    check("nothing lost in the split", "\n\n".join(pieces) == long_text)
    check("safe() hides a bot token", "123456:ABC" not in watch.safe("error at /bot123456:ABC-def_ghi/sendMessage"))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
