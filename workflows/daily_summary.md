# Daily Summary

**Objective:** Every day at 21:00 local time, produce a short chronological
timeline of what was actually accomplished that day across every project in
the workspace — meant to be skimmable in a few seconds to judge whether the
day was productive. Not a diffstat dump.

## Trigger

Windows Task Scheduler task `WAT-DailySummary`, runs daily at 21:00, calls:

```
python tools/daily_summary/format_report.py
```

## Tools used

- `tools/daily_summary/collect.py` — walks the workspace root, finds the
  top-level repo plus every nested project folder that has its own `.git`
  (checked by `os.path.isdir(<folder>/.git)`), and for each one pulls today's
  commits (`git log --since/--until --author=<user email>`, hash + time +
  subject only) plus a count of uncommitted paths (`git status --porcelain`).
  For folders with no `.git`, it walks the tree and lists files whose mtime
  falls today. Writes structured JSON, not formatted text, so the formatter
  can freely re-sort/re-group without re-parsing text.
- `tools/daily_summary/format_report.py` — calls `collect.py`, merges every
  project's commits into **one cross-project timeline sorted by time**
  (commit subject lines are the "what did I accomplish" signal — that's
  what people write them for), dedupes identical commit hashes that show up
  in more than one repo, and reduces non-git folder activity to one line
  ("N files edited, no git history") instead of a file list. Uncommitted
  work becomes a single "still in progress" line naming the projects, not a
  path listing.

## Output

`.tmp/daily_summaries/<YYYY-MM-DD>.md` — disposable per WAT convention, but
kept around as a daily log; nothing prunes old ones yet. Example:

```
# Daily Summary — 2026-08-31

## Timeline

- **08:21** [mapflow-crm] Add optional monthly fee to pricing tiers
- **15:21** [talentflow] Add advanced actor profiles, privacy/legal center, and two-step booking wizard
- **18:46** [talentflow] Add search box to filter talent in the New Booking actor picker

## Still in progress (uncommitted)

wat-framework, art-rock-dental, mapflow-crm, mashtatech
```

## Known limitations

- Author filtering uses the git config email (`myanir4@gmail.com`). If commits
  are made under a different local git identity, they won't show up — check
  `git config user.email` in the relevant repo if a day's commits go missing.
- No AI narration step. The `claude` CLI isn't on PATH in this environment
  (this session runs via the VSCode extension), so the report is a structured
  data dump, not a prose summary. If the CLI becomes available later, wiring
  `claude -p` in as a post-processing step over the raw file is the natural
  upgrade — see `.tmp/daily_summaries/<date>_raw.txt` for the ungrouped input.
- Projects that are plain folders (not git repos) only get an mtime-based
  file count, not a description of what changed inside those files — the
  timeline can't say what was accomplished there, only that something was
  touched.
- Two different commits with the same subject line (e.g. booking-platform's
  history was squashed/re-committed once when it was split into its own
  repo) show up as two timeline entries even though hash-based dedup catches
  true duplicates. Cosmetic, not worth solving for a one-time migration.
- The task only runs if the machine is on and awake at 21:00. Task Scheduler
  is configured to run on battery and wake the machine if needed (see setup
  below), but a fully powered-off machine will still miss the run.
