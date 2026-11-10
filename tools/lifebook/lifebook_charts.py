"""
Inline SVG charts for the book, drawn in millimetres so they print at true size.

Colour rules (validated with the dataviz palette checker against white paper):
  - Mood is ordinal, so it uses a diverging scale: cool blue arm for low/rough,
    warm orange arm for good/amazing, neutral gray for okay. Each arm passes the
    ordinal checks; adjacent steps clear CVD dE 14.1 and normal-vision dE 16.6.
    Mood is never colour-only: every chart that uses it ships a labelled legend.
  - Everything that isn't mood (habits, day score) is drawn in ink, so the only
    colour in the book means "how the day felt".
"""

from __future__ import annotations

import calendar
import datetime as dt
from html import escape

from lifebook_data import MOODS, Book, Month

MOOD_COLORS = {
    "rough": "#2a78d6",
    "low": "#86b6ef",
    "okay": "#dddbd4",
    "good": "#ef9a72",
    "amazing": "#c4521f",
}
MOOD_TEXT_ON = {"rough": "#ffffff", "amazing": "#ffffff"}   # fills dark enough for white numerals

INK = "#24211d"
INK_2 = "#5b5650"
MUTED = "#8d877d"
HAIR = "#e3e0d8"
RING = "#cfcac0"
WASH = "#f4f2ed"

PT = 0.3528  # mm per point


def _svg(width: float, height: float, body: list[str], label: str) -> str:
    return (f'<svg class="viz" role="img" aria-label="{escape(label)}" xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width:.2f} {height:.2f}" width="{width:.2f}mm" height="{height:.2f}mm">'
            + "".join(body) + "</svg>")


def _text(x, y, s, size_pt=6.5, anchor="start", fill=INK_2, weight=400, extra=""):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size_pt * PT:.2f}" text-anchor="{anchor}" '
            f'fill="{fill}" font-weight="{weight}" {extra}>{escape(str(s))}</text>')


def _text_width(s: str, size_pt: float) -> float:
    return len(s) * size_pt * PT * 0.56


def _fit(s: str, size_pt: float, max_w: float) -> str:
    if _text_width(s, size_pt) <= max_w:
        return s
    while s and _text_width(s + "…", size_pt) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def _bar_path(x, y, w, h, r_left, r_right):
    """A horizontal bar with independently rounded left/right ends."""
    r_left, r_right = min(r_left, w / 2, h / 2), min(r_right, w / 2, h / 2)
    return (f'<path d="M{x + r_left:.2f},{y:.2f} H{x + w - r_right:.2f} '
            f'Q{x + w:.2f},{y:.2f} {x + w:.2f},{y + r_right:.2f} V{y + h - r_right:.2f} '
            f'Q{x + w:.2f},{y + h:.2f} {x + w - r_right:.2f},{y + h:.2f} H{x + r_left:.2f} '
            f'Q{x:.2f},{y + h:.2f} {x:.2f},{y + h - r_left:.2f} V{y + r_left:.2f} '
            f'Q{x:.2f},{y:.2f} {x + r_left:.2f},{y:.2f} Z"')


# ── mood ───────────────────────────────────────────────────────────────────

def mood_bar(counts: dict, width: float, height: float = 3.4) -> str:
    """100% stacked bar, rough → amazing, 0.5 mm paper gaps between segments."""
    total = sum(counts.get(m, 0) for m in MOODS)
    if not total:
        return ""
    present = [m for m in MOODS if counts.get(m)]
    gap = 0.5
    usable = width - gap * (len(present) - 1)
    x, body = 0.0, []
    for i, m in enumerate(present):
        w = usable * counts[m] / total
        body.append(_bar_path(x, 0, w, height, 0.9 if i == 0 else 0, 0.9 if i == len(present) - 1 else 0)
                    + f' fill="{MOOD_COLORS[m]}"/>')
        x += w + gap
    return _svg(width, height, body, "Mood mix: " + ", ".join(f"{m} {counts[m]}" for m in present))


def year_in_pixels(book: Book, width: float) -> str:
    """One row per month, one square per day of the month, filled with that day's mood."""
    label_w, axis_h = 9.0, 4.2
    pitch = (width - label_w) / 31
    gap = max(0.35, pitch * 0.14)
    cell = pitch - gap
    body = []
    for d in (1, 5, 10, 15, 20, 25, 31):
        body.append(_text(label_w + (d - 1) * pitch + cell / 2, axis_h - 1.4, d, 5.5, "middle", MUTED))
    for row, month in enumerate(book.months):
        y = axis_h + row * pitch
        body.append(_text(0, y + cell * 0.78, month.name[:3], 6, "start", INK_2))
        for d in range(1, calendar.monthrange(month.year, month.month)[1] + 1):
            date = dt.date(month.year, month.month, d)
            x = label_w + (d - 1) * pitch
            day = book.days.get(date)
            if day is None:
                continue
            if day.mood:
                body.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="0.45" '
                            f'fill="{MOOD_COLORS[day.mood]}"/>')
            else:
                body.append(f'<rect x="{x + 0.12:.2f}" y="{y + 0.12:.2f}" width="{cell - 0.24:.2f}" '
                            f'height="{cell - 0.24:.2f}" rx="0.45" fill="none" stroke="{RING}" stroke-width="0.22"/>')
    height = axis_h + len(book.months) * pitch
    return _svg(width, height, body, "Year in pixels: each day coloured by mood")


def month_calendar(book: Book, month: Month, width: float, week_start: int) -> str:
    """A wall-calendar for the month: mood fill, date, day score and a mark on milestone days."""
    gap, head_h, cell_h = 0.9, 4.0, 10.5
    cell_w = (width - 6 * gap) / 7
    names = [calendar.day_abbr[(week_start + i) % 7][:2] for i in range(7)]
    body = [_text(i * (cell_w + gap) + 0.4, head_h - 1.3, n, 6, "start", MUTED, 500) for i, n in enumerate(names)]
    first = dt.date(month.year, month.month, 1)
    offset = (first.weekday() - week_start) % 7
    n_days = calendar.monthrange(month.year, month.month)[1]
    rows = (offset + n_days + 6) // 7
    milestone_days = {e.date for e in month.stats["milestones"]}
    for d in range(1, n_days + 1):
        date = dt.date(month.year, month.month, d)
        idx = offset + d - 1
        x = (idx % 7) * (cell_w + gap)
        y = head_h + (idx // 7) * (cell_h + gap)
        day = book.days.get(date)
        num_fill = INK
        if day is None:                                   # outside the book's range: number only
            num_fill = "#c9c4ba"
        elif day.mood:
            body.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" rx="0.8" '
                        f'fill="{MOOD_COLORS[day.mood]}"/>')
            num_fill = MOOD_TEXT_ON.get(day.mood, INK)
        else:
            body.append(f'<rect x="{x + 0.15:.2f}" y="{y + 0.15:.2f}" width="{cell_w - 0.3:.2f}" height="{cell_h - 0.3:.2f}" '
                        f'rx="0.8" fill="none" stroke="{RING}" stroke-width="0.25"/>')
        body.append(_text(x + 1.1, y + 3.1, d, 7, "start", num_fill, 600))
        if day is not None and day.day_score is not None:
            body.append(_text(x + cell_w - 1.0, y + cell_h - 1.2, day.day_score, 5.5, "end", num_fill, 400,
                              'opacity="0.85"'))
        if date in milestone_days:
            body.append(_text(x + cell_w - 1.0, y + 3.1, "★", 7, "end", num_fill, 400))
    height = head_h + rows * (cell_h + gap) - gap
    return _svg(width, height, body, f"{month.title}: calendar coloured by mood")


# ── day score ──────────────────────────────────────────────────────────────

def day_score_chart(book: Book, width: float, height: float = 46.0) -> str:
    points = sorted((d, s) for d, day in book.days.items() for s in [day.day_score] if s is not None)
    if len(points) < 3:
        return ""
    left, bottom, top = 7.0, 5.0, 3.5
    plot_w, plot_h = width - left - 2.0, height - bottom - top
    first, last = points[0][0], points[-1][0]     # only the stretch where scores exist
    span = max(1, (last - first).days)

    def X(d):
        return left + plot_w * (d - first).days / span

    def Y(v):
        return top + plot_h * (1 - v / 100)

    body = []
    for v in (0, 25, 50, 75, 100):
        body.append(f'<line x1="{left:.2f}" x2="{left + plot_w:.2f}" y1="{Y(v):.2f}" y2="{Y(v):.2f}" '
                    f'stroke="{HAIR if v else RING}" stroke-width="{0.15 if v else 0.22}"/>')
        body.append(_text(left - 1.4, Y(v) + 0.8, v, 5.5, "end", MUTED))
    ticks = [(X(max(first, dt.date(m.year, m.month, 1))), m.name[:3]) for m in book.months
             if (first.year, first.month) <= (m.year, m.month) <= (last.year, last.month)]
    if len(ticks) > 1 and ticks[1][0] - ticks[0][0] < 7:
        ticks = ticks[1:]                                 # a partial first month would collide
    for x, name in ticks:
        if x <= left + plot_w - 4:
            body.append(_text(x, height - 1.0, name, 5.5, "start", MUTED))
    for d, s in points:
        body.append(f'<circle cx="{X(d):.2f}" cy="{Y(s):.2f}" r="0.6" fill="{INK}" fill-opacity="0.25"/>')

    # rolling average of the last 7 scores (from the 3rd one on), broken where scoring
    # stopped for more than 10 days
    window, line, segments, run = 7, [], [], []
    for i, (d, s) in enumerate(points):
        if i and (d - points[i - 1][0]).days > 10:
            if line:
                segments.append(line)
            line, run = [], []
        run.append(s)
        if len(run) >= 3:
            chunk = run[-window:]
            line.append((X(d), Y(sum(chunk) / len(chunk))))
    if line:
        segments.append(line)
    for seg in segments:
        if len(seg) > 1:
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in seg)
            body.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="0.5" '
                        f'stroke-linejoin="round" stroke-linecap="round"/>')

    bd, bs = max(points, key=lambda p: p[1])
    bx, by = X(bd), Y(bs)
    body.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="1.0" fill="{INK}" stroke="#fff" stroke-width="0.5"/>')
    label = f"Best: {bs} on {bd.day} {calendar.month_abbr[bd.month]}"
    anchor = "end" if bx > left + plot_w * 0.7 else "start"
    body.append(_text(bx + (-1.8 if anchor == "end" else 1.8), by + 1.0, label, 6, anchor, INK, 600))
    return _svg(width, height, body, "Day score over time, with a 7-check-in rolling average")


# ── habits ─────────────────────────────────────────────────────────────────

def habit_bars(book: Book, width: float) -> str:
    habits = sorted(book.habits, key=lambda h: (-h.rate, h.name))
    if not habits:
        return ""
    fs, row, bar_h = 6.5, 6.6, 2.6
    name_w = min(width * 0.36, max(_text_width(h.name, fs) for h in habits) + 3.5)
    streak_w = 11.0
    bar_max = width - name_w - streak_w - 9.0
    body = [_text(width, 2.6, "Best run", 5.5, "end", MUTED, 500)]
    for i, h in enumerate(habits):
        y = 4.5 + i * row
        mark = "◆ " if h.core else ""
        body.append(_text(0, y + bar_h - 0.2, mark + _fit(h.name, fs, name_w - 3.5), fs, "start", INK))
        body.append(_bar_path(name_w, y, bar_max, bar_h, 0, 1.0) + f' fill="{WASH}"/>')
        w = max(0.8, bar_max * h.rate)
        body.append(_bar_path(name_w, y, w, bar_h, 0, 1.0) + f' fill="{INK}"/>')
        body.append(_text(name_w + w + 1.2, y + bar_h - 0.25, f"{round(h.rate * 100)}%", fs, "start", INK, 600))
        body.append(_text(width, y + bar_h - 0.25, f"{h.longest_streak} d", fs, "end", INK_2))
    height = 4.5 + len(habits) * row - (row - bar_h)
    return _svg(width, height, body, "Habit completion since each habit was added")


def habit_grid(book: Book, month: Month, width: float, week_start: int) -> str:
    """Habits x days of the month: a dot where the habit was checked off."""
    n_days = calendar.monthrange(month.year, month.month)[1]
    first, last = dt.date(month.year, month.month, 1), dt.date(month.year, month.month, n_days)
    habits = [h for h in book.habits if h.start <= min(last, book.end) and h.start <= book.end]
    if not habits or not any(book.days[d].habits_possible for d in month.dates):
        return ""
    fs = 6.0
    name_w = min(width * 0.3, max(_text_width(h.name, fs) for h in habits) + 2.5)
    count_w = 8.0
    pitch = (width - name_w - count_w) / n_days
    row = max(pitch, 3.0)
    axis_h = 4.0
    weekend = {(week_start + 5) % 7, (week_start + 6) % 7}
    body = []
    height = axis_h + len(habits) * row
    for d in range(1, n_days + 1):
        date = dt.date(month.year, month.month, d)
        x = name_w + (d - 1) * pitch
        if date.weekday() in weekend:
            body.append(f'<rect x="{x:.2f}" y="{axis_h - 0.6:.2f}" width="{pitch:.2f}" '
                        f'height="{height - axis_h + 0.6:.2f}" fill="{WASH}"/>')
        if d in (1, 5, 10, 15, 20, 25, n_days):
            body.append(_text(x + pitch / 2, axis_h - 1.3, d, 5.5, "middle", MUTED))
    for i, h in enumerate(habits):
        cy = axis_h + i * row + row / 2
        body.append(_text(0, cy + 0.75, _fit(h.name, fs, name_w - 2.0), fs, "start", INK))
        done = possible = 0
        for d in range(1, n_days + 1):
            date = dt.date(month.year, month.month, d)
            if date not in book.days or date < h.start:
                continue
            possible += 1
            cx = name_w + (d - 1) * pitch + pitch / 2
            if date in h.done:
                done += 1
                body.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{min(pitch, row) * 0.36:.2f}" fill="{INK}"/>')
            else:
                body.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="0.28" fill="{RING}"/>')
        body.append(_text(width, cy + 0.75, f"{done}/{possible}" if possible else "", fs, "end", INK_2))
    return _svg(width, height, body, f"{month.title}: habits checked off each day")
