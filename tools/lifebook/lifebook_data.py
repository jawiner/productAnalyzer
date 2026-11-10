"""
Turns a Lifemaxing (Base44) export JSON into the model the book is rendered from.

Everything here is deterministic: it only reorganises, filters and counts what is
already in the export. No text is generated.

Entities used:
    JournalEntry, Habit, HabitLog, WorkoutSession, ProgressiveOverload,
    PunchClockSession, Task, MonthlyPlan, TrainingGoal, ChallengeConfig,
    LearningProject, LifeBook (only its cover photo, as the default cover)
Ignored: StreakState, LifeBookChapter, EventCounter and the empty log types.
Rows flagged is_sample (the app's demo data) are always dropped.
"""

from __future__ import annotations

import calendar
import datetime as dt
import difflib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

MOODS = ["rough", "low", "okay", "good", "amazing"]
VIDEO_EXT = {".mov", ".mp4", ".m4v", ".webm", ".avi", ".3gp", ".mkv"}
AUTO_WORKOUT = "__habit_auto__"

GOAL_TYPES = {
    "triathlon_70_3": "Half Ironman 70.3",
    "triathlon_full": "Ironman",
    "triathlon_olympic": "Olympic triathlon",
    "triathlon_sprint": "Sprint triathlon",
    "marathon": "Marathon",
    "half_marathon": "Half marathon",
    "10k": "10K run",
    "5k": "5K run",
}

WORKOUT_NAMES = {
    "run": "Run", "swim": "Swim", "bike": "Ride", "ride": "Ride", "cycling": "Ride",
    "strength": "Strength", "brick": "Brick", "yoga": "Yoga", "walk": "Walk", "hike": "Hike",
}


# ── helpers ────────────────────────────────────────────────────────────────

def parse_date(value) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def norm_name(name: str) -> str:
    return (name or "").replace("’", "'").replace("‘", "'").strip().casefold()


def fmt_minutes(minutes: float) -> str:
    minutes = int(round(minutes or 0))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} h {m} min"
    if h:
        return f"{h} h"
    return f"{m} min"


def fmt_num(n) -> str:
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.1f}"
    return f"{int(n):,}"


def fmt_day(d: dt.date) -> str:
    return f"{d.day} {calendar.month_name[d.month]}"


def fmt_full_date(d: dt.date) -> str:
    return f"{d.day} {calendar.month_name[d.month]} {d.year}"


def fmt_span(start: dt.date, end: dt.date) -> str:
    if start.year == end.year:
        if start.month == end.month:
            return f"{calendar.month_name[start.month]} {start.year}"
        return f"{calendar.month_name[start.month]} – {calendar.month_name[end.month]} {end.year}"
    return (f"{calendar.month_name[start.month]} {start.year} – "
            f"{calendar.month_name[end.month]} {end.year}")


def is_video(url: str) -> bool:
    path = url.split("?")[0].lower()
    return os.path.splitext(path)[1] in VIDEO_EXT


def paragraphs(text: str) -> list[str]:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    return [p.strip() for p in text.split("\n") if p.strip()]


def word_count(text: str) -> int:
    return len((text or "").split())


# ── model ──────────────────────────────────────────────────────────────────

@dataclass
class Entry:
    id: str
    date: dt.date
    mood: str | None
    day_score: int | None
    paragraphs: list[str]
    words: int
    insight: str
    milestone: str | None          # milestone summary when the day is flagged as one
    goals_tomorrow: list[str]
    goals_review: list[tuple[str, bool]]
    photo_urls: list[str]
    video_count: int
    created: str


@dataclass
class Habit:
    id: str
    name: str
    icon: str
    created: dt.date
    sort_order: float
    core: bool = False              # a required habit in the app's challenge
    done: set = field(default_factory=set)
    notes: dict = field(default_factory=dict)
    start: dt.date | None = None    # first day it counts toward completion
    possible: int = 0
    rate: float = 0.0
    longest_streak: int = 0
    longest_streak_end: dt.date | None = None


@dataclass
class Day:
    date: dt.date
    entries: list[Entry] = field(default_factory=list)
    habits_done: list[str] = field(default_factory=list)
    habits_possible: int = 0
    habit_notes: list[tuple[str, str]] = field(default_factory=list)
    workouts: list[dict] = field(default_factory=list)
    gym: list[dict] = field(default_factory=list)
    clocked: list[dict] = field(default_factory=list)
    tasks_done: list[dict] = field(default_factory=list)

    @property
    def mood(self) -> str | None:
        for e in self.entries:
            if e.mood:
                return e.mood
        return None

    @property
    def day_score(self) -> int | None:
        scores = [e.day_score for e in self.entries if e.day_score is not None]
        return scores[-1] if scores else None

    @property
    def has_ledger(self) -> bool:
        return bool(self.habits_possible or self.habit_notes or self.workouts or self.gym
                    or self.clocked or self.tasks_done)


@dataclass
class Month:
    key: str
    year: int
    month: int
    index: int
    dates: list[dt.date]            # every date of this month inside the book's range
    days: list[Day]                 # only days that have journal entries
    stats: dict = field(default_factory=dict)
    plan: dict | None = None
    hero_url: str | None = None
    hero_date: dt.date | None = None

    @property
    def name(self) -> str:
        return calendar.month_name[self.month]

    @property
    def title(self) -> str:
        return f"{self.name} {self.year}"


@dataclass
class Book:
    title: str
    subtitle: str
    author: str
    start: dt.date
    end: dt.date
    source_name: str
    generated: dt.date
    months: list[Month]
    days: dict                      # date -> Day (every date in range)
    habits: list[Habit]
    stats: dict
    insights: list[tuple[dt.date, str]]
    milestones: list[tuple[dt.date, str, str | None]]
    training_goals: list[dict]
    open_tasks: list[dict]
    projects: list[dict]
    challenge: dict | None
    cover_url: str | None
    photo_urls: list[str]           # every photo, in date order
    hidden_habits: list[str]
    reflections_count: int = 0


# ── loading ────────────────────────────────────────────────────────────────

def _rows(data: dict, name: str) -> list[dict]:
    rows = data.get(name) or []
    return [r for r in rows if isinstance(r, dict) and not r.get("is_sample")]


def _merge_duplicates(entries: list[dict]) -> list[dict]:
    """Same-day entries that are drafts or near-identical resubmissions collapse into one."""
    by_date = defaultdict(list)
    for e in entries:
        by_date[e.get("date")].append(e)
    out = []
    for date, group in by_date.items():
        group.sort(key=lambda e: e.get("created_date") or "")
        kept: list[dict] = []
        for e in group:
            text = (e.get("text") or "").strip()
            has_media = bool(e.get("media_urls") or e.get("photo_url"))
            if not text and not has_media and not e.get("insight") and not e.get("submitted", True):
                continue                                   # an empty unsubmitted draft
            twin = None
            for k in kept:
                kt = (k.get("text") or "").strip()
                if text and kt and difflib.SequenceMatcher(None, text, kt).quick_ratio() > 0.9 \
                        and difflib.SequenceMatcher(None, text, kt).ratio() > 0.9:
                    twin = k
                    break
            if twin is None:
                kept.append(dict(e))
                continue
            # keep the later version's text and mood, but never lose a photo
            later, earlier = (e, twin) if (e.get("updated_date") or "") >= (twin.get("updated_date") or "") else (twin, e)
            merged = dict(later)
            media = list(later.get("media_urls") or [])
            for u in (earlier.get("media_urls") or []):
                if u not in media:
                    media.append(u)
            merged["media_urls"] = media
            merged["photo_url"] = later.get("photo_url") or earlier.get("photo_url")
            for k in ("insight", "milestone_summary"):
                merged[k] = later.get(k) or earlier.get(k)
            merged["is_milestone"] = bool(later.get("is_milestone") or earlier.get("is_milestone"))
            kept[kept.index(twin)] = merged
        out.extend(kept)
    return out


def _entry(raw: dict) -> Entry:
    urls = []
    for u in [raw.get("photo_url")] + list(raw.get("media_urls") or []):
        if u and u not in urls:
            urls.append(u)
    photos = [u for u in urls if not is_video(u)]
    mood = (raw.get("mood") or "").strip().lower() or None
    if mood not in MOODS:
        mood = None
    review = []
    for g in raw.get("goals_review") or []:
        if isinstance(g, dict) and (g.get("text") or "").strip():
            review.append((g["text"].strip(), bool(g.get("completed"))))
        elif isinstance(g, str) and g.strip():
            review.append((g.strip(), False))
    milestone = None
    if raw.get("is_milestone"):
        milestone = (raw.get("milestone_summary") or "").strip() or "A milestone day"
    score = raw.get("day_score")
    return Entry(
        id=raw.get("id", ""),
        date=parse_date(raw.get("date")),
        mood=mood,
        day_score=int(score) if isinstance(score, (int, float)) else None,
        paragraphs=paragraphs(raw.get("text")),
        words=word_count(raw.get("text")),
        insight=(raw.get("insight") or "").strip(),
        milestone=milestone,
        goals_tomorrow=[g.strip() for g in (raw.get("goals_tomorrow") or []) if isinstance(g, str) and g.strip()],
        goals_review=review,
        photo_urls=photos,
        video_count=len(urls) - len(photos),
        created=raw.get("created_date") or "",
    )


def _workout(raw: dict) -> dict | None:
    desc = (raw.get("description") or "").strip()
    metrics = ["distance_km", "duration_minutes", "pace_seconds_per_km", "avg_heart_rate",
               "elevation_gain_m", "avg_watts", "avg_speed_kmh", "calories_burned", "rpe"]
    has_data = any(raw.get(k) for k in metrics) or raw.get("how_i_felt") or (desc and desc != AUTO_WORKOUT)
    if not has_data:
        return None                     # logged automatically by ticking the Workout habit
    kind = (raw.get("workout_type") or "workout").lower()
    name = WORKOUT_NAMES.get(kind, kind.replace("_", " ").capitalize())
    sub = (raw.get("workout_subtype") or "").strip()
    if sub:
        name += f" ({sub.replace('_', ' ')})"
    parts = []
    dist = raw.get("distance_km")
    if dist:
        parts.append(f"{dist * 1000:.0f} m" if kind == "swim" and dist < 2 else f"{dist:g} km")
    if raw.get("duration_minutes"):
        parts.append(fmt_minutes(raw["duration_minutes"]))
    pace = raw.get("pace_seconds_per_km")
    if pace and kind == "run":
        parts.append(f"{int(pace) // 60}:{int(pace) % 60:02d} /km")
    if raw.get("avg_speed_kmh") and kind != "run":
        parts.append(f"{raw['avg_speed_kmh']:g} km/h")
    if raw.get("elevation_gain_m"):
        parts.append(f"↑ {raw['elevation_gain_m']:,.0f} m")
    if raw.get("avg_watts"):
        parts.append(f"{raw['avg_watts']:.0f} W")
    if raw.get("avg_heart_rate"):
        parts.append(f"avg HR {raw['avg_heart_rate']:.0f}")
    if raw.get("rpe"):
        parts.append(f"RPE {raw['rpe']:g}")
    notes = [n for n in [(raw.get("how_i_felt") or "").strip(),
                         desc if desc != AUTO_WORKOUT else ""] if n]
    return {"name": name, "detail": " · ".join(parts), "notes": notes,
            "kind": kind, "distance": dist or 0}


def _sets(sets: list) -> str:
    sets = [s for s in (sets or []) if isinstance(s, dict) and s.get("reps")]
    if not sets:
        return ""
    weights = {s.get("weight_kg") for s in sets}
    if len(weights) == 1:
        w = next(iter(weights))
        reps = " · ".join(str(s["reps"]) for s in sets)
        return f"{w:g} kg × {reps}" if w else f"reps {reps}"
    return " · ".join(f"{(s.get('weight_kg') or 0):g}×{s['reps']}" for s in sets)


def _longest_streak(dates: set) -> tuple[int, dt.date | None]:
    best, best_end, run, prev = 0, None, 0, None
    for d in sorted(dates):
        run = run + 1 if prev and (d - prev).days == 1 else 1
        if run > best:
            best, best_end = run, d
        prev = d
    return best, best_end


def load_book(path: str | Path, *, start: dt.date | None = None, end: dt.date | None = None,
              title: str | None = None, subtitle: str | None = None, author: str = "",
              cover: str | None = None, hide_habits: list[str] | None = None) -> Book:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "JournalEntry" not in data:
        raise ValueError("This doesn't look like a Lifemaxing export: no JournalEntry list at the top level.")

    raw_entries = [e for e in _rows(data, "JournalEntry") if parse_date(e.get("date"))]
    habit_logs = [h for h in _rows(data, "HabitLog") if h.get("completed", True) and parse_date(h.get("date"))]

    all_dates = [parse_date(e["date"]) for e in raw_entries] or [parse_date(h["date"]) for h in habit_logs]
    if not all_dates:
        raise ValueError("The export has no dated journal entries or habit logs.")
    start = start or min(all_dates)
    end = end or max(all_dates)
    if end < start:
        raise ValueError(f"--to ({end}) is before --from ({start}).")

    def in_range(d):
        return d is not None and start <= d <= end

    # ── habits ──
    hidden = {norm_name(h) for h in (hide_habits or [])}
    habit_rows = _rows(data, "Habit")
    known = {norm_name(h.get("name", "")) for h in habit_rows}
    unknown_hidden = [h for h in (hide_habits or []) if norm_name(h) not in known
                      and h not in {r.get("id") for r in habit_rows}]
    if unknown_hidden:
        names = ", ".join(sorted(h.get("name", "") for h in habit_rows))
        raise ValueError(f"--hide-habit didn't match {unknown_hidden}. Habits in this export: {names}")
    hidden_ids = {h["id"] for h in habit_rows
                  if norm_name(h.get("name", "")) in hidden or h.get("id") in (hide_habits or [])}

    challenge_raw = next((c for c in _rows(data, "ChallengeConfig") if c.get("active")), None)
    core_ids = set((challenge_raw or {}).get("required_habit_ids") or [])

    habits: dict[str, Habit] = {}
    for h in habit_rows:
        if h["id"] in hidden_ids or h.get("active") is False:
            continue
        habits[h["id"]] = Habit(
            id=h["id"], name=(h.get("name") or "Habit").strip(), icon=h.get("icon") or "",
            created=parse_date(h.get("created_date")) or start,
            sort_order=h.get("sort_order") or 0, core=h["id"] in core_ids)

    checkins = 0
    for log in habit_logs:
        d = parse_date(log["date"])
        if not in_range(d) or log.get("habit_id") in hidden_ids:
            continue
        checkins += 1
        habit = habits.get(log.get("habit_id"))
        if habit is None:
            continue
        habit.done.add(d)
        note = (log.get("description") or "").strip()
        if note:
            habit.notes[d] = note

    for habit in habits.values():
        first = min(habit.done) if habit.done else habit.created
        habit.start = max(start, min(habit.created, first))
        habit.possible = max(0, (end - habit.start).days + 1) if habit.start <= end else 0
        habit.rate = len(habit.done) / habit.possible if habit.possible else 0.0
        habit.longest_streak, habit.longest_streak_end = _longest_streak(habit.done)
    habit_list = sorted(habits.values(), key=lambda h: (h.sort_order, h.name))
    habit_list = [h for h in habit_list if h.possible]

    # ── days ──
    days: dict[dt.date, Day] = {}
    d = start
    while d <= end:
        day = Day(date=d)
        active = [h for h in habit_list if h.start <= d]
        day.habits_possible = len(active)
        day.habits_done = [h.name for h in active if d in h.done]
        day.habit_notes = [(h.name, h.notes[d]) for h in habit_list if d in h.notes]
        days[d] = day
        d += dt.timedelta(days=1)

    entries = [_entry(e) for e in _merge_duplicates(raw_entries)]
    entries = [e for e in entries if in_range(e.date)
               and (e.paragraphs or e.photo_urls or e.insight or e.milestone or e.goals_tomorrow
                    or e.goals_review or e.mood or e.day_score is not None)]
    entries.sort(key=lambda e: (e.date, e.created))
    for e in entries:
        days[e.date].entries.append(e)

    workouts_logged, distance = 0, 0.0
    for w in _rows(data, "WorkoutSession"):
        wd = parse_date(w.get("date"))
        if not in_range(wd):
            continue
        workouts_logged += 1
        info = _workout(w)
        if info:
            days[wd].workouts.append(info)
            distance += info["distance"] or 0

    gym_by_date = defaultdict(list)
    for p in _rows(data, "ProgressiveOverload"):
        pd = parse_date(p.get("session_date"))
        if in_range(pd):
            muscle = p.get("other_muscle") if p.get("muscle_group") == "other" else p.get("muscle_group")
            gym_by_date[pd].append({"exercise": (p.get("exercise_name") or "Exercise").strip(),
                                    "sets": _sets(p.get("sets")), "muscle": (muscle or "").strip(),
                                    "notes": (p.get("notes") or "").strip()})
    for gd, rows in gym_by_date.items():
        days[gd].gym = rows

    deep_minutes, clocked_minutes = 0, 0
    for p in sorted(_rows(data, "PunchClockSession"), key=lambda p: p.get("start_time") or ""):
        pd = parse_date(p.get("date"))
        if not in_range(pd):
            continue
        minutes = p.get("duration_minutes") or 0
        label = (p.get("label") or "Session").strip()
        clocked_minutes += minutes
        if "deep" in label.lower():
            deep_minutes += minutes
        days[pd].clocked.append({"label": label, "minutes": minutes,
                                 "duration": fmt_minutes(minutes),
                                 "summary": (p.get("summary") or "").strip()})

    tasks_done, open_tasks = 0, []
    for t in _rows(data, "Task"):
        title_ = (t.get("title") or "").strip()
        if not title_:
            continue
        folder = (t.get("folder") or "").strip()
        if t.get("status") == "done":
            cd = parse_date(t.get("completed_at"))
            if in_range(cd):
                tasks_done += 1
                days[cd].tasks_done.append({"title": title_, "folder": folder})
        else:
            open_tasks.append({"title": title_, "folder": folder,
                               "due": parse_date(t.get("due_date")), "priority": t.get("priority") or ""})
    open_tasks.sort(key=lambda t: (t["due"] or dt.date.max, t["title"]))

    # ── months ──
    months: list[Month] = []
    month_keys = sorted({(d.year, d.month) for d in days})
    plans = {p.get("month"): p for p in _rows(data, "MonthlyPlan") if p.get("month")}
    for i, (y, m) in enumerate(month_keys, start=1):
        dates = [d for d in days if d.year == y and d.month == m]
        mdays = [days[d] for d in dates if days[d].entries]
        month = Month(key=f"{y}-{m:02d}", year=y, month=m, index=i, dates=dates, days=mdays)
        month.plan = _plan(plans.get(month.key))
        months.append(month)

    # ── book-wide ──
    entry_list = [e for day in days.values() for e in day.entries]
    photo_urls = [u for e in entry_list for u in e.photo_urls]
    mood_counts = Counter(day.mood for day in days.values() if day.entries and day.mood)
    scored = [(day.date, day.day_score) for day in days.values() if day.day_score is not None]
    best = max(scored, key=lambda s: s[1]) if scored else None
    streak_habit = max(habit_list, key=lambda h: h.longest_streak, default=None)

    insights = [(e.date, e.insight) for e in entry_list if e.insight]
    milestones = [(e.date, e.milestone, e.photo_urls[0] if e.photo_urls else None)
                  for e in entry_list if e.milestone]

    goals = []
    for g in _rows(data, "TrainingGoal"):
        if g.get("active") is False:
            continue
        td = parse_date(g.get("target_date"))
        kind = g.get("goal_type") or ""
        goals.append({"name": GOAL_TYPES.get(kind, kind.replace("_", " ").capitalize() or "Goal"),
                      "target_date": td, "target_time": (g.get("target_time") or "").strip(),
                      "description": (g.get("goal_description") or "").strip(),
                      "days_out": (td - end).days if td else None,
                      "upcoming": bool(td and td > end)})
    goals.sort(key=lambda g: g["target_date"] or dt.date.max)

    projects = [{"title": (p.get("title") or "").strip(), "description": (p.get("description") or "").strip(),
                 "status": p.get("status") or "", "start": parse_date(p.get("start_date")),
                 "end": parse_date(p.get("end_date"))}
                for p in _rows(data, "LearningProject") if (p.get("title") or "").strip()]

    challenge = None
    if challenge_raw:
        by_id = {h.id: h.name for h in habit_list}
        challenge = {"start": parse_date(challenge_raw.get("start_date")),
                     "required": [by_id[i] for i in challenge_raw.get("required_habit_ids") or [] if i in by_id],
                     "optional": [by_id[i] for i in challenge_raw.get("optional_habit_ids") or [] if i in by_id]}

    cover_url = cover
    if not cover_url:
        books = sorted(_rows(data, "LifeBook"), key=lambda b: b.get("updated_date") or "", reverse=True)
        cover_url = next((b.get("cover_image_url") for b in books if b.get("cover_image_url")), None)

    days_journaled = sum(1 for day in days.values() if day.entries)
    stats = {
        "span_days": (end - start).days + 1,
        "days_journaled": days_journaled,
        "entries": len(entry_list),
        "words": sum(e.words for e in entry_list),
        "photos": len(photo_urls),
        "videos": sum(e.video_count for e in entry_list),
        "checkins": checkins,
        "workouts": workouts_logged,
        "distance_km": round(distance, 1),
        "gym_sessions": len(gym_by_date),
        "milestones": len(milestones),
        "insights": len(insights),
        "deep_minutes": deep_minutes,
        "clocked_minutes": clocked_minutes,
        "tasks_done": tasks_done,
        "mood_counts": {m: mood_counts.get(m, 0) for m in MOODS},
        "avg_score": round(sum(s for _, s in scored) / len(scored)) if scored else None,
        "scored_days": len(scored),
        "score_since": min(d for d, _ in scored) if scored else None,
        "best_day": best,
        "streak_habit": streak_habit,
    }

    if not title:
        title = f"{days_journaled} Days"
    if subtitle is None:
        subtitle = f"A Lifemaxing journal · {fmt_span(start, end)}"

    book = Book(
        title=title, subtitle=subtitle, author=author, start=start, end=end,
        source_name=path.name, generated=dt.date.today(), months=months, days=days,
        habits=habit_list, stats=stats, insights=insights, milestones=milestones,
        training_goals=goals, open_tasks=open_tasks, projects=projects, challenge=challenge,
        cover_url=cover_url, photo_urls=photo_urls,
        hidden_habits=[h.get("name") for h in habit_rows if h["id"] in hidden_ids],
    )
    for month in months:
        _month_stats(book, month)
    book.reflections_count = sum(1 for m in months if m.plan and m.plan.get("reflection"))
    return book


def _plan(raw: dict | None) -> dict | None:
    if not raw:
        return None
    fields = [("Life direction", raw.get("life_direction")), ("Goals", raw.get("goals")),
              ("Achievements I'm aiming for", raw.get("achievements")),
              ("New habits", raw.get("new_habits")), ("Notes", raw.get("description"))]
    intentions = [(label, paragraphs(text)) for label, text in fields if (text or "").strip()]
    prompts = [p.strip() for p in raw.get("ai_reflection_prompts") or [] if isinstance(p, str) and p.strip()]
    reflection = (raw.get("ai_summary") or "").strip()
    if not (intentions or prompts or reflection):
        return None
    return {"intentions": intentions, "prompts": prompts, "reflection": reflection}


def _month_stats(book: Book, month: Month) -> None:
    entries = [e for day in month.days for e in day.entries]
    moods = Counter(day.mood for day in month.days if day.mood)
    done = sum(len(book.days[d].habits_done) for d in month.dates)
    possible = sum(book.days[d].habits_possible for d in month.dates)
    scores = [day.day_score for day in month.days if day.day_score is not None]
    month.stats = {
        "entries": len(month.days),
        "words": sum(e.words for e in entries),
        "photos": sum(len(e.photo_urls) for e in entries),
        "mood_counts": {m: moods.get(m, 0) for m in MOODS},
        "habit_rate": done / possible if possible else None,
        "workouts": sum(len(book.days[d].workouts) for d in month.dates),
        "gym_days": sum(1 for d in month.dates if book.days[d].gym),
        "deep_minutes": sum(c["minutes"] for d in month.dates for c in book.days[d].clocked
                            if "deep" in c["label"].lower()),
        "tasks_done": sum(len(book.days[d].tasks_done) for d in month.dates),
        "milestones": [e for e in entries if e.milestone],
        "avg_score": round(sum(scores) / len(scores)) if scores else None,
    }
    month.hero_url, month.hero_date = _pick_hero(month)


def _pick_hero(month: Month) -> tuple[str | None, dt.date | None]:
    """Milestone photos first, then the best-scored / happiest days that have photos."""
    rank = {m: i for i, m in enumerate(MOODS)}
    candidates = []
    for day in month.days:
        for e in day.entries:
            if e.photo_urls:
                candidates.append(((1 if e.milestone else 0), e.day_score or -1,
                                   rank.get(e.mood or "", -1), e.date, e))
    if not candidates:
        return None, None
    candidates.sort(key=lambda c: c[:4], reverse=True)
    e = candidates[0][4]
    return e.photo_urls[0], e.date
