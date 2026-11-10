"""
Builds a printable PDF book from a Lifemaxing app export.

Usage:
    python tools/lifebook/build_lifebook.py <export.json> [options]

Common options:
    --out PATH              where to write the PDF (default: next to the export,
                            e.g. lifemaxing-export-2026-10-02.json -> lifemaxing-book-2026-10-02.pdf)
    --title / --subtitle / --author
    --cover URL_OR_PATH     cover photo (default: the cover chosen in the app's LifeBook)
    --from / --to YYYY-MM-DD   only include this date range
    --hide-habit NAME       leave a habit (and its notes) out of the book; repeatable
    --size a5|6x9|a4        page size (default a5)
    --week-start sunday|monday
    --photo-px N            longest edge of embedded photos (default 1400 = ~300 dpi at A5 width)
    --no-photos             text-and-charts-only edition
    --html-only             stop after writing the HTML (fast layout iteration)
    --open                  open the PDF when done

Intermediates live in .tmp/lifebook/ (photo cache + build/book.html) and can be deleted.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import html
import logging
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

import lifebook_charts as charts  # noqa: E402
from lifebook_data import MOODS, Book, fmt_full_date, fmt_num, fmt_span, load_book, parse_date  # noqa: E402
from lifebook_photos import Photo, fetch_photos  # noqa: E402

SIZES = {
    "a5":  dict(w=148.0, h=210.0, mt=17, mb=19, ms=16, body_pt=10.2, cover_pt=54, sheet_cols=8),
    "6x9": dict(w=152.4, h=228.6, mt=18, mb=20, ms=17, body_pt=10.4, cover_pt=56, sheet_cols=8),
    "a4":  dict(w=210.0, h=297.0, mt=24, mb=26, ms=24, body_pt=11.0, cover_pt=72, sheet_cols=10),
}
PHOTO_GAP = 1.2
logging.getLogger("pypdf").setLevel(logging.ERROR)   # Chromium PDFs trip a harmless xref-size warning
WEEKDAY = {"monday": 0, "sunday": 6}
END_TITLES = ("Things I learned", "Looking ahead", "Every photo")


# ── template filters ───────────────────────────────────────────────────────

def _day_month(d: dt.date) -> str:
    return f"{d.day} {calendar.month_name[d.month]}" if d else ""


def _weekday(d: dt.date) -> str:
    return calendar.day_name[d.weekday()] if d else ""


def _clock_summary(sessions: list[dict]) -> list[dict]:
    """Punch-clock sessions grouped by label, in the order they first happened."""
    grouped: dict[str, dict] = {}
    for s in sessions:
        key = s["label"].casefold()
        g = grouped.setdefault(key, {"label": s["label"], "minutes": 0, "summaries": []})
        g["minutes"] += s["minutes"] or 0
        if s["summary"] and s["summary"] not in g["summaries"]:
            g["summaries"].append(s["summary"])
    out = []
    for g in grouped.values():
        h, m = divmod(int(round(g["minutes"])), 60)
        g["duration"] = f"{h} h {m} min" if h and m else (f"{h} h" if h else f"{m} min")
        out.append(g)
    return out


def _inline_md(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return text


def _markdown(text: str) -> str:
    """The small Markdown subset the app's AI summaries use: headings, lists, bold, italics."""
    lines = text.replace("\r\n", "\n").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^\s*(#{1,6}\s|\*\*.+\*\*\s*$)", lines[0]):
        lines.pop(0)                      # the summary's own title repeats our heading
    out, para, list_tag = [], [], None

    def flush_para():
        if para:
            out.append(f'<p dir="auto">{_inline_md(" ".join(para))}</p>')
            para.clear()

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            close_list()
            continue
        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        bullet = re.match(r"^[-*•]\s+(.*)$", line)
        numbered = re.match(r"^\d+[.)]\s+(.*)$", line)
        if heading:
            flush_para()
            close_list()
            out.append(f"<h4>{_inline_md(heading.group(1))}</h4>")
        elif bullet or numbered:
            flush_para()
            tag = "ul" if bullet else "ol"
            if list_tag != tag:
                close_list()
                out.append(f"<{tag}>")
                list_tag = tag
            out.append(f'<li dir="auto">{_inline_md((bullet or numbered).group(1))}</li>')
        else:
            close_list()
            para.append(line)
    flush_para()
    close_list()
    return "\n".join(out)


# ── layout helpers ─────────────────────────────────────────────────────────

def photo_rows(photos: list[Photo], width: float, gap: float = PHOTO_GAP) -> list[list[dict]]:
    """Justified rows: every photo keeps its shape, each row fills the column width."""
    if not photos:
        return []
    target, max_row, max_single = width * 0.45, width * 0.7, width * 0.72

    def sized(row, h):
        return [{"photo": p, "w": h * p.aspect, "h": h} for p in row]

    if len(photos) == 1:
        p = photos[0]
        h = min(width / p.aspect, max_single)
        return [sized([p], h)]
    rows, cur = [], []
    for p in photos:
        cur.append(p)
        h = (width - gap * (len(cur) - 1)) / sum(x.aspect for x in cur)
        if h <= target or len(cur) == 4:
            rows.append(sized(cur, h))
            cur = []
    if cur:
        h = (width - gap * (len(cur) - 1)) / sum(x.aspect for x in cur)
        rows.append(sized(cur, min(h, max_row if len(cur) > 1 else max_single)))
    return rows


def stat_tiles(book: Book) -> list[dict]:
    s = book.stats
    tiles = [
        {"label": "Days written down", "value": fmt_num(s["days_journaled"]),
         "sub": f"of {s['span_days']} days"},
        {"label": "Words written", "value": fmt_num(s["words"]),
         "sub": f"about {round(s['words'] / max(1, s['days_journaled'])):,} a day"},
        {"label": "Photos", "value": fmt_num(s["photos"]),
         "sub": f"plus {s['videos']} videos" if s["videos"] else ""},
        {"label": "Habit check-ins", "value": fmt_num(s["checkins"]),
         "sub": f"across {len(book.habits)} habits"},
        {"label": "Workouts logged", "value": fmt_num(s["workouts"]),
         "sub": f"{s['distance_km']:g} km recorded" if s["distance_km"] else ""},
    ]
    if s["deep_minutes"]:
        tiles.append({"label": "Deep work clocked", "value": f"{s['deep_minutes'] / 60:.0f} h",
                      "sub": f"of {s['clocked_minutes'] / 60:.0f} h on the punch clock"})
    if s["tasks_done"]:
        tiles.append({"label": "Tasks crossed off", "value": fmt_num(s["tasks_done"]),
                      "sub": f"{len(book.open_tasks)} still open" if book.open_tasks else ""})
    tiles.append({"label": "Milestones", "value": fmt_num(s["milestones"]),
                  "sub": f"and {s['insights']} insights" if s["insights"] else ""})
    if s["streak_habit"] and s["streak_habit"].longest_streak > 1:
        h = s["streak_habit"]
        tiles.append({"label": "Longest streak", "value": f"{h.longest_streak} days",
                      "sub": f"{h.name}, to {_day_month(h.longest_streak_end)}"})
    if s["best_day"]:
        d, score = s["best_day"]
        tiles.append({"label": "Best day score", "value": str(score),
                      "sub": f"on {_day_month(d)} · average {s['avg_score']}"})
    if len(tiles) % 2:
        tiles = tiles[:-1] if len(tiles) > 8 else tiles
    return tiles


def build_charts(book: Book, cw: float, week_start: int) -> dict:
    out = {
        "pixels": charts.year_in_pixels(book, cw),
        "mood_bar": charts.mood_bar(book.stats["mood_counts"], cw),
        "score": charts.day_score_chart(book, cw),
        "habits": charts.habit_bars(book, cw),
        "months": {},
    }
    for m in book.months:
        out["months"][m.key] = {
            "mood_bar": charts.mood_bar(m.stats["mood_counts"], cw, 3.0),
            "calendar": charts.month_calendar(book, m, cw, week_start),
            "grid": charts.habit_grid(book, m, cw, week_start),
        }
    return out


def render_html(env: Environment, book: Book, photos: dict[str, Photo], size: str,
                week_start: int, toc: dict) -> str:
    g = dict(SIZES[size])
    g["cw"] = g["w"] - 2 * g["ms"]
    hero_urls = {m.hero_url for m in book.months if m.hero_url and m.hero_url in photos}
    rows = {}
    for day in book.days.values():
        for e in day.entries:
            shown = [photos[u] for u in e.photo_urls if u in photos and u not in hero_urls]
            rows[e.id] = photo_rows(shown, g["cw"])
    last_entry = next((e for d in sorted(book.days, reverse=True) for e in reversed(book.days[d].entries)), None)
    last_goals = last_entry.goals_tomorrow if last_entry else []
    has_ahead = bool(book.training_goals or book.open_tasks or book.projects or last_goals)
    sheet = [photos[u] for u in dict.fromkeys(book.photo_urls) if u in photos]
    end_titles = [t for t, present in zip(END_TITLES, (book.insights, has_ahead, sheet)) if present]
    heads = ([{"name": "p-glance", "label": "At a glance"}]
             + [{"name": f"m-{m.key}", "label": m.title} for m in book.months]
             + [{"name": n, "label": t} for n, t in
                zip(("p-insights", "p-ahead", "p-photos"), END_TITLES)])
    cover = photos.get(book.cover_url) if book.cover_url else None
    if cover is None:
        cover = next((photos[m.hero_url] for m in book.months if m.hero_url in photos), None)
    def pg(title: str) -> str:
        return str(toc.get(_toc_key(title), "00"))

    return env.get_template("book.html.j2").render(
        book=book, photos=photos, page=g, moods=MOODS, mood_colors=charts.MOOD_COLORS, pg=pg,
        charts=build_charts(book, g["cw"], week_start), tiles=stat_tiles(book),
        photo_rows=rows, photo_gap=PHOTO_GAP, sheet=sheet, sheet_cols=g["sheet_cols"],
        running_heads=heads, end_titles=end_titles, toc=toc, cover=cover,
        span_label=fmt_span(book.start, book.end), last_goals=last_goals, has_ahead=has_ahead)


def make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(HERE / "templates"),
                      autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=False, lstrip_blocks=False)
    env.filters.update(full_date=lambda d: fmt_full_date(d) if d else "", day_month=_day_month,
                       weekday=_weekday, markdown=_markdown, clock_summary=_clock_summary)
    return env


# ── PDF ────────────────────────────────────────────────────────────────────

def _toc_key(title: str) -> str:
    # Chromium drops the space between inline spans in outline titles ("April2026"),
    # so contents lookups compare titles with all whitespace removed.
    return re.sub(r"\s+", "", title)


def _outline_pages(pdf_path: Path) -> tuple[dict, int]:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    pages = {}
    for item in reader.outline:
        if isinstance(item, list):
            continue
        pages.setdefault(_toc_key(str(item.title)), reader.get_destination_page_number(item) + 1)
    return pages, len(reader.pages)


def render_pdf(env, book, photos, size, week_start, html_path: Path, pdf_path: Path, log=print) -> int:
    from playwright.sync_api import sync_playwright
    toc: dict = {}
    raw_pdf = html_path.with_suffix(".pdf")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(600_000)
        for attempt in range(1, 4):
            html_path.write_text(render_html(env, book, photos, size, week_start, toc), encoding="utf-8")
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.evaluate("document.fonts.ready.then(() => true)")
            log(f"  printing pass {attempt}…")
            page.pdf(path=str(raw_pdf), prefer_css_page_size=True, print_background=True,
                     outline=True, tagged=True)
            found, n_pages = _outline_pages(raw_pdf)
            new_toc = {k: v for k, v in found.items()}
            if new_toc == toc:
                break
            toc = new_toc
        browser.close()

    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter(clone_from=PdfReader(str(raw_pdf)))
    writer.add_metadata({
        "/Title": book.title,
        "/Subject": book.subtitle or "",
        "/Author": book.author or "",
        "/Creator": "Lifemaxing book builder (WAT tools/lifebook)",
    })
    writer.page_mode = "/UseOutlines"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    raw_pdf.unlink(missing_ok=True)
    return n_pages


def default_out(src: Path) -> Path:
    stem = src.stem
    name = stem.replace("export", "book") if "export" in stem else f"{stem}-book"
    return src.with_name(f"{name}.pdf")


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn a Lifemaxing export into a printable PDF book.")
    ap.add_argument("export", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--subtitle")
    ap.add_argument("--author", default="")
    ap.add_argument("--cover", help="photo URL or local path for the cover")
    ap.add_argument("--from", dest="date_from")
    ap.add_argument("--to", dest="date_to")
    ap.add_argument("--hide-habit", action="append", default=[], metavar="NAME")
    ap.add_argument("--size", choices=sorted(SIZES), default="a5")
    ap.add_argument("--week-start", choices=sorted(WEEKDAY), default="sunday")
    ap.add_argument("--photo-px", type=int, default=1400)
    ap.add_argument("--no-photos", action="store_true")
    ap.add_argument("--html-only", action="store_true")
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    if not args.export.exists():
        print(f"Export not found: {args.export}", file=sys.stderr)
        return 2
    started = time.time()
    try:
        book = load_book(args.export, start=parse_date(args.date_from), end=parse_date(args.date_to),
                         title=args.title, subtitle=args.subtitle, author=args.author,
                         cover=args.cover, hide_habits=args.hide_habit)
    except ValueError as e:
        print(f"Can't build the book: {e}", file=sys.stderr)
        return 2
    s = book.stats
    print(f"Loaded {s['entries']} entries, {s['checkins']} habit check-ins, {s['photos']} photos "
          f"({book.start} → {book.end}, {len(book.months)} chapter{'s' if len(book.months) != 1 else ''})")

    photos: dict[str, Photo] = {}
    if not args.no_photos:
        urls = list(book.photo_urls) + ([book.cover_url] if book.cover_url else [])
        print(f"Preparing {len(set(urls))} photos (cached after the first run)…")
        photos = fetch_photos(urls, ROOT / ".tmp" / "lifebook" / "photos", max_px=args.photo_px)

    build_dir = ROOT / ".tmp" / "lifebook" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    html_path = build_dir / "book.html"
    env = make_env()
    week_start = WEEKDAY[args.week_start]

    if args.html_only:
        html_path.write_text(render_html(env, book, photos, args.size, week_start, {}), encoding="utf-8")
        print(f"HTML written: {html_path}")
        return 0

    out = args.out or default_out(args.export)
    print("Rendering PDF…")
    n_pages = render_pdf(env, book, photos, args.size, week_start, html_path, out)
    size_mb = out.stat().st_size / 1_048_576
    print(f"Done in {time.time() - started:.0f}s: {out}  ({n_pages} pages, {size_mb:.1f} MB)")
    if args.open and hasattr(os, "startfile"):
        os.startfile(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
