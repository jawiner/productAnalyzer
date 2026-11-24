"""
Pure alert rules for the expiry watcher: when to warn, what to say.
No network, no Notion, no clock (today is always passed in), so test_offline.py
can check every case.
"""

import calendar
import html
import re
from datetime import date

T_SUBSCRIPTION = "Subscription"
T_DOMAIN = "Domain"
T_SSL = "SSL certificate"
T_TOKEN = "API key / token"
T_LICENCE = "Licence"
T_MEMBERSHIP = "Membership"
T_OTHER = "Other"
TYPES = [T_SUBSCRIPTION, T_DOMAIN, T_SSL, T_TOKEN, T_LICENCE, T_MEMBERSHIP, T_OTHER]

R_ONCE = "One-time"
R_MONTHLY = "Monthly"
R_YEARLY = "Yearly"
REPEATS = [R_ONCE, R_MONTHLY, R_YEARLY]

DEFAULT_WARN = [30, 14, 7, 3, 1, 0]


def default_warn(item_type: str, repeats: str, auto_renew: bool) -> list[int]:
    """Days before the date on which a warning goes out, when the row doesn't set its own."""
    if auto_renew and repeats == R_MONTHLY:
        return [3, 1]
    if auto_renew and repeats == R_YEARLY:
        return [14, 3, 1]
    if repeats == R_MONTHLY:
        return [3, 1, 0]
    if item_type == T_SSL:
        # Hosts renew certificates by themselves about 30 days ahead, so a warning
        # only makes sense once that has clearly not happened.
        return [14, 7, 3, 1, 0]
    return DEFAULT_WARN


def parse_warn(text: str) -> list[int] | None:
    """'30, 7, 1' -> [30, 7, 1]. Anything without numbers -> None (use the default)."""
    days = sorted({int(n) for n in re.findall(r"\d+", text or "") if int(n) <= 730}, reverse=True)
    return days or None


def renews_itself(auto_renew: bool, repeats: str) -> bool:
    return bool(auto_renew) and repeats in (R_MONTHLY, R_YEARLY)


def add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def roll_forward(expires: date, repeats: str, today: date) -> date:
    """Next renewal date of something that renews by itself, once the old date has passed.
    Counted from the original date, so the 31st doesn't drift to the 28th for good."""
    step = {R_MONTHLY: 1, R_YEARLY: 12}.get(repeats)
    if not step or expires >= today:
        return expires
    k = 1
    while add_months(expires, step * k) < today:
        k += 1
    return add_months(expires, step * k)


def stage(days_left: int, warn: list[int]) -> str | None:
    """Which warning the item is at. None = too far away to mention.

    Before the date: the tightest warning day already reached ('7' covers days 7..4
    when the list is 30,14,7,3,1,0). After it: late1, late2, late3, then one per week.
    A new stage means one new alert, so a PC that was off for days sends one message
    with the real number of days, not a backlog.
    """
    if days_left >= 0:
        reached = [t for t in warn if t >= days_left]
        return str(min(reached)) if reached else None
    late = -days_left
    if late <= 3:
        return f"late{late}"
    weeks = (late - 3) // 7
    return "late3" if weeks == 0 else f"late-week{weeks}"


def marker(expires: date, stage_name: str) -> str:
    """Stored in the row's 'Last alert'. Tied to the date, so a renewed item starts over."""
    return f"{expires.isoformat()}|{stage_name}"


def problem_marker(today: date) -> str:
    """A broken key or certificate alerts once, then once a week while it stays broken."""
    year, week, _ = today.isocalendar()
    return f"problem|{year}-W{week:02d}"


def when_text(days_left: int, auto: bool) -> str:
    verb = "Renews by itself" if auto else "Expires"
    if days_left > 1:
        return f"{verb} in {days_left} days"
    if days_left == 1:
        return f"{verb} tomorrow"
    if days_left == 0:
        return f"{verb} today"
    if days_left == -1:
        return "Expired yesterday"
    return f"Expired {-days_left} days ago"


def nice_date(d: date) -> str:
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b %Y')}"


def status_text(*, problem: str | None, note: str | None, expires: date | None,
                days_left: int | None, stage_name: str | None, auto: bool,
                healthy: bool = False) -> str:
    """Short text for the row's Status column. No day counts in it (the 'Days left'
    column counts live), so it only changes when the state does.
    healthy = an automatic check passed today (a key that works has no date to show)."""
    if problem:
        return f"🔴 {problem}"
    if expires is None:
        if note:
            return f"{'🟢' if healthy else '⚪'} {note}"
        return "⚪ No date yet"
    if days_left < 0:
        text = "🔴 Expired"
    elif stage_name is None:
        text = "🟢 OK"
    elif days_left <= 3:
        text = "🔴 Renews very soon" if auto else "🔴 Expires very soon"
    else:
        text = "🟡 Renews soon" if auto else "🟡 Expires soon"
    return f"{text} · {note}" if note else text


def _icon(days_left: int | None, problem: bool) -> str:
    if problem or (days_left is not None and days_left <= 3):
        return "🔴"
    return "🟡"


def format_digest(alerts: list[dict], today: date) -> str:
    """One Telegram message (HTML) for everything that needs attention today.
    Each alert: name, type, expires, days_left, auto, problem, cost, link, notes."""
    alerts = sorted(alerts, key=lambda a: (a.get("days_left") is None, a.get("days_left") or 0))
    count = len(alerts)
    head = "1 thing needs attention" if count == 1 else f"{count} things need attention"
    lines = [f"⏰ <b>Renewals: {head}</b>"]
    for a in alerts:
        lines.append("")
        lines.append(f"{_icon(a.get('days_left'), bool(a.get('problem')))} "
                     f"<b>{html.escape(a['name'])}</b> · {html.escape(a['type'] or T_OTHER)}")
        if a.get("problem"):
            lines.append(html.escape(a["problem"]))
        else:
            detail = f"{when_text(a['days_left'], a['auto'])} ({nice_date(a['expires'])})"
            if a.get("cost"):
                detail += f" · {a['cost']}"
            lines.append(html.escape(detail))
        if a.get("notes"):
            lines.append(html.escape(a["notes"][:300]))
        if a.get("link"):
            lines.append(f"Renew: {html.escape(a['link'])}")
    return "\n".join(lines)


def format_heartbeat(upcoming: list[dict], no_date: int, unknown: int, today: date) -> str:
    """Weekly 'still watching' message, so silence never means the watcher died."""
    lines = ["✅ <b>Renewal check is running</b>"]
    if upcoming:
        lines.append("")
        lines.append("Next up:")
        for u in upcoming[:5]:
            lines.append(f"• {html.escape(u['name'])}: "
                         f"{html.escape(when_text(u['days_left'], u['auto']).lower())} ({nice_date(u['expires'])})")
    else:
        lines.append("Nothing with a date on the list yet.")
    if no_date:
        lines.append("")
        lines.append(f"{no_date} row{'s' if no_date != 1 else ''} on the list "
                     f"{'have' if no_date != 1 else 'has'} no date, so I can't warn about "
                     f"{'them' if no_date != 1 else 'it'}.")
    if unknown:
        lines.append(f"{unknown} automatic check{'s' if unknown != 1 else ''} couldn't be done today.")
    return "\n".join(lines)
