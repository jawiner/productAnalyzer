# Build a Lifemaxing Book

**Objective:** Turn a Lifemaxing app export (the JSON you download from the app's
settings, e.g. `lifemaxing-export-2026-10-02.json`) into a printable PDF book: the
full journal, grouped into monthly chapters, with photos, mood and habit charts,
milestones, insights and what was still ahead. Every word in it comes from the
export. Nothing is generated and no API credits are used.

## Trigger

On request ("make a book from this export"). Usually the export lands in
`~/Downloads`, and the book is written next to it.

## Inputs

- **Required:** path to the export JSON.
- **Optional:** title, subtitle, author, cover photo, date range, habits to hide,
  page size. Ask only if the user mentions them. The defaults produce a complete book.

## Run

```
python tools/lifebook/build_lifebook.py "C:/Users/97254/Downloads/lifemaxing-export-YYYY-MM-DD.json"
```

Output: `lifemaxing-book-YYYY-MM-DD.pdf` in the same folder (override with `--out`).
Give the user the PDF path, page count and size that the script prints.

Useful options:

| Option | Effect |
|---|---|
| `--title "…" --subtitle "…" --author "…"` | Cover and title page text. Default title is "N Days" (days written down); the subtitle is the month span. |
| `--cover URL_OR_PATH` | Cover photo. Default: the cover picked in the app's own LifeBook, else the first chapter's hero photo. |
| `--from 2026-07-01 --to 2026-09-30` | A book for just that range (a quarter, a year…). |
| `--hide-habit "Name"` (repeatable) | Removes a habit from charts, counts and daily notes, for a copy you'll share. Straight and curly apostrophes both match. It does **not** edit journal text that mentions the habit. |
| `--size a5\|6x9\|a4` | Page size. A5 (default) and 6x9 are standard print-on-demand book sizes. |
| `--week-start sunday\|monday` | Calendar layout. Default Sunday (Israeli week). |
| `--no-photos` | Text and charts only. Much smaller file. |
| `--photo-px N` | Photo resolution. 1400 ≈ 300 dpi at A5 width. Lower it for a smaller screen-only file. |
| `--html-only` | Writes `.tmp/lifebook/build/book.html` and stops. Use it for fast layout iteration. |
| `--open` | Opens the PDF when done. |

## Tools used

- `tools/lifebook/lifebook_data.py` loads the export and builds the model: days,
  monthly chapters, habit rates and streaks, stats. It drops `is_sample` demo rows
  and empty unsubmitted drafts, and merges same-day resubmissions (text ≥ 90%
  similar), keeping every photo.
- `tools/lifebook/lifebook_photos.py` downloads each photo once to
  `.tmp/lifebook/photos/orig/`, then makes EXIF-rotated print copies and thumbnails.
  Re-runs are instant. Videos (.mov/.mp4) can't go in a PDF, so they're counted and
  noted instead.
- `tools/lifebook/lifebook_charts.py` draws the inline SVG charts: year in pixels,
  mood mix bars, day score, habit completion bars, and each month's calendar and
  habit grid.
- `tools/lifebook/build_lifebook.py` is the CLI. It renders
  `templates/book.html.j2` + `book.css.j2` and prints the PDF with Playwright
  Chromium.

## What the book contains

1. Cover, title page, and contents with real page numbers.
2. **At a glance:** headline numbers, year in pixels (mood per day), mood mix, day
   score trend, habit completion and best streaks, milestones.
3. **One chapter per month:** a photo opener with the month's stats and mood mix; a
   month-at-a-glance page (mood calendar and habit dot grid); the month's plan from
   `MonthlyPlan`; then every entry verbatim. Each entry shows its mood, score,
   milestone, photos (justified rows, never cropped), insight, goals, and a footer
   with habits, training, gym sets, punch-clock time, tasks finished that day and
   habit notes. The chapter ends with the app's monthly reflection
   (`MonthlyPlan.ai_summary`), labelled as written by the app.
4. **End matter:** every insight; looking ahead (upcoming races from `TrainingGoal`,
   open tasks, projects); a contact sheet of every photo; a colophon.

Ignored on purpose: `StreakState` (snapshots with no habit link; streaks are
recomputed from `HabitLog`), `LifeBook`/`LifeBookChapter` (the app's older
generated book; only its cover photo is reused) and `EventCounter`.

## Design notes

- Mood is the only colour in the book. It uses a diverging scale (blue for rough/low,
  gray for okay, orange for good/amazing), validated with the dataviz palette
  checker against white paper. Everything else is ink.
- Fonts load from Google Fonts at render time (Newsreader, Inter, and Frank Ruhl
  Libre / Heebo for Hebrew). Offline, it falls back to Georgia/Segoe UI and still
  builds.
- Hebrew paragraphs are set right-to-left automatically (`dir="auto"`).

## Edge cases and lessons

- **Contents page numbers** come from a two-pass print. Pass 1 prints with
  placeholders; the PDF outline (headings) gives each section's page; pass 2 prints
  with real numbers; the loop stops when the numbers are stable. Chromium drops the
  space between inline spans in outline titles ("April2026"), so titles are
  compared with all whitespace removed.
- Chromium 151 supports `@page` margin boxes (page numbers), named pages (running
  heads per chapter, full-bleed cover and openers) and `outline=True`. If an older
  Chromium ever shows no page numbers, run `python -m playwright install chromium`.
- Entries with no text but with a mood or score are real check-ins and are kept
  (shown as "No words this day, just the check-in.").
- Expect about 60–100 s for a six-month export with ~220 photos. The first run adds
  ~2 min for photo downloads. The PDF is ~40 MB with photos; `--photo-px 1000`
  roughly halves that for screen reading.
- `.tmp/lifebook/` is disposable. Deleting it just means photos re-download.
