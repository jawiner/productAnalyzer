"""The video playbook on the video PC (used by worker.py; only the standard library).

  study_next()     takes the next thing the owner sent (a link, a video file or text), gets it ready
                   with study_prep.py (speech venv: download, transcript, cuts, frames), has Claude
                   study it headless with study_rules.md, and reports the proposed lessons back; the
                   content-engine function sends them to the owner on Telegram to add or skip.
  sync_playbook()  writes the lessons the owner added into ~/.claude/skills/video-playbook, the skill
                   every video job reads (the daily videos via rules.md, and any other video work).
  remake_next()    an ad the owner wants "one like this" of: Claude breaks it down second by second
                   (remake_rules.md) and writes an original idea for the brand in the same format; the
                   function sends it to the owner as a remake idea (motion graphics or AI footage).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
STUDIES = ROOT / ".tmp" / "content_studio" / "studies"
SPEECH_PY = ROOT / ".tmp" / "venv-speech" / "Scripts" / "python.exe"
PREP = HERE / "study_prep.py"
STUDY_RULES = HERE / "study_rules.md"
REMAKE_RULES = HERE / "remake_rules.md"
SKILL_DIR = Path.home() / ".claude" / "skills" / "video-playbook"
YTDLP_STAMP = ROOT / ".tmp" / "content_studio" / "yt-dlp-updated.txt"
STUDY_MODEL = "claude-opus-5-5"
STUDY_EFFORT = "medium"
STUDY_TIMEOUT_S = 25 * 60
REMAKE_EFFORT = "high"
PREP_TIMEOUT_S = 45 * 60
KEEP_DAYS = 21
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

TOPICS = {
    "hook": "Hook (the first 3 seconds)", "story": "Story", "pacing": "Pacing", "visuals": "Visuals",
    "on_screen_text": "On-screen text", "voice_sound": "Voice and sound", "ending_cta": "Ending and ask",
    "caption": "Caption and hashtags", "posting": "Posting and growth", "other": "Other",
}
PLATFORMS = {
    "tiktok": "TikTok", "instagram": "Instagram", "youtube": "YouTube", "facebook": "Facebook", "x": "X",
    "linkedin": "LinkedIn", "threads": "Threads", "web": "web page", "telegram": "video file", "text": "text",
}

_LESSON = {
    "type": "object", "additionalProperties": False,
    "required": ["topic", "rule", "why", "example", "relation", "related_number"],
    "properties": {
        "topic": {"type": "string", "enum": list(TOPICS)},
        "rule": {"type": "string"}, "why": {"type": "string"}, "example": {"type": "string"},
        "relation": {"type": "string", "enum": ["new", "supports", "conflicts"]},
        "related_number": {"type": "integer"},
    },
}
STUDY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["title", "creator", "summary", "craft_notes", "lessons"],
    "properties": {
        "title": {"type": "string"}, "creator": {"type": "string"}, "summary": {"type": "string"},
        "craft_notes": {"type": "string"}, "lessons": {"type": "array", "items": _LESSON},
    },
}


_THEIR_BEAT = {
    "type": "object", "additionalProperties": False,
    "required": ["start_s", "end_s", "job", "visual", "text_on_screen", "audio"],
    "properties": {"start_s": {"type": "number"}, "end_s": {"type": "number"}, "job": {"type": "string"},
                   "visual": {"type": "string"}, "text_on_screen": {"type": "string"}, "audio": {"type": "string"}},
}
_STR = {"type": "string"}
_OUR_BEAT = {"type": "object", "additionalProperties": False, "required": ["say", "show", "mirrors"],
             "properties": {"say": _STR, "show": _STR, "mirrors": _STR}}
_FACT = {"type": "object", "additionalProperties": False, "required": ["claim", "source"], "properties": {"claim": _STR, "source": _STR}}
_IDEA_KEYS = ["title", "pillar", "formula", "hook_line", "on_screen_hook", "concept", "beats", "facts", "caption_seed", "why"]
# Mirrors REMAKE_SCHEMA in the CRM's supabase/functions/_shared/contentCopy.js.
REMAKE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["format", "hook", "their_beats", "route", "route_reason", "idea"],
    "properties": {
        "format": _STR, "hook": _STR, "their_beats": {"type": "array", "items": _THEIR_BEAT},
        "route": {"type": "string", "enum": ["motion", "ai_footage"]}, "route_reason": _STR,
        "idea": {"type": "object", "additionalProperties": False, "required": _IDEA_KEYS, "properties": {
            **{k: _STR for k in _IDEA_KEYS if k not in ("beats", "facts")},
            "beats": {"type": "array", "items": _OUR_BEAT}, "facts": {"type": "array", "items": _FACT},
        }},
    },
}


class Ctx:
    """What the worker hands over: its engine client, log, claude binary and child environment."""

    def __init__(self, engine, log, claude_bin: str, child_env: dict):
        self.engine, self.log, self.claude, self.child_env = engine, log, claude_bin, child_env


# ---- Getting it ready -----------------------------------------------------------------------

def _run_prep(args: list[str], folder: Path, offline: bool) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PYTHONUTF8"] = "1"
    if offline:
        env["HF_HUB_OFFLINE"] = "1"   # the speech models are on this PC; don't ask the hub every time
    (folder / "packet.json").unlink(missing_ok=True)
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=PREP_TIMEOUT_S, env=env, creationflags=NO_WINDOW)
    (folder / "prep.log").write_text((proc.stdout or "") + "\n" + (proc.stderr or "")[-20000:], encoding="utf-8")
    path = folder / "packet.json"
    if not path.exists():
        return {"error": f"study_prep stopped (exit {proc.returncode})", "code": "prep"}
    return json.loads(path.read_text(encoding="utf-8"))


def _update_ytdlp_once(ctx: Ctx) -> bool:
    """Sites change and yt-dlp follows: on a download error, update it (at most once a day)."""
    today = f"{dt.date.today():%Y-%m-%d}"
    if YTDLP_STAMP.exists() and YTDLP_STAMP.read_text(encoding="utf-8").strip() == today:
        return False
    YTDLP_STAMP.parent.mkdir(parents=True, exist_ok=True)
    YTDLP_STAMP.write_text(today, encoding="utf-8")
    proc = subprocess.run([str(SPEECH_PY), "-m", "pip", "install", "-q", "-U", "yt-dlp[default,curl-cffi]"],
                          capture_output=True, text=True, timeout=600, creationflags=NO_WINDOW)
    ctx.log(f"yt-dlp update: {'ok' if proc.returncode == 0 else 'failed ' + (proc.stderr or '')[-300:]}")
    return proc.returncode == 0


def _suffix(source: dict) -> str:
    name = (source.get("file_name") or "").lower()
    if "." in name and len(name.rsplit(".", 1)[1]) <= 4:
        return "." + name.rsplit(".", 1)[1]
    return {"video/quicktime": ".mov", "video/webm": ".webm", "video/x-matroska": ".mkv"}.get(source.get("mime") or "", ".mp4")


def gather(ctx: Ctx, source: dict, folder: Path) -> dict:
    if source["kind"] == "text":
        (folder / "page.txt").write_text(source.get("body") or "", encoding="utf-8")
        return {"kind": "text"}
    args = [str(SPEECH_PY), "-X", "utf8", "-I", str(PREP), "--out", str(folder)]
    if source["kind"] == "file":
        target = folder / "media" / f"upload{_suffix(source)}"
        target.parent.mkdir(parents=True, exist_ok=True)
        ctx.engine.download("source_file", target, source_id=source["id"])
        args += ["--file", str(target)]
    else:
        args += ["--url", source["url"]]
    packet = _run_prep(args, folder, offline=True)
    if packet.get("code") == "prep" and "offline" in str(packet.get("error", "")).lower():
        packet = _run_prep(args, folder, offline=False)
    if packet.get("code") == "download" and source["kind"] == "link" and _update_ytdlp_once(ctx):
        packet = _run_prep(args, folder, offline=True)
    return packet


def _fmt_count(n) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return ""
    return f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.1f}K" if v >= 1e3 else str(int(v))


def _source_lines(source: dict, packet: dict) -> list[str]:
    """What the PC knows about a source: where it's from, the site's data, the measurements, the files."""
    site = packet.get("site") or {}
    origin = {"link": f"{PLATFORMS.get(source.get('platform'), 'web')} link {source.get('url')}",
              "file": f"a video file sent on Telegram ({source.get('file_name') or 'no name'})",
              "text": "a text the owner pasted"}[source["kind"]]
    lines = [f"Source: {origin}", f"Sent: {str(source.get('created_at') or '')[:10]}"]
    lines += [f"The owner's note: \"{source['note']}\"" if source.get("note") else "The owner didn't add a note.", ""]
    if site:
        lines += ["## What the site says about it (untrusted)", ""]
        if site.get("title"):
            lines.append(f"Title: {site['title']}")
        who = site.get("uploader") or site.get("creator") or ""
        channel = site.get("channel") or ""
        if who or channel:
            lines.append(f"Creator: {who}" + (f" ({channel})" if channel and channel != who else ""))
        stats = [f"posted {site['upload_date'][:4]}-{site['upload_date'][4:6]}-{site['upload_date'][6:]}" if site.get("upload_date") else "",
                 f"{_fmt_count(site.get('view_count'))} views" if site.get("view_count") else "",
                 f"{_fmt_count(site.get('like_count'))} likes" if site.get("like_count") else "",
                 f"{_fmt_count(site.get('comment_count'))} comments" if site.get("comment_count") else ""]
        if any(stats):
            lines.append("Numbers: " + ", ".join(s for s in stats if s))
        if site.get("description"):
            lines.append(f"Description: {str(site['description'])[:1500]}")
        lines.append("")
    if packet.get("kind") == "video":
        sp, cuts = packet.get("speech") or {}, packet.get("cuts") or {}
        lines += ["## What the PC measured", "",
                  f"Length {packet.get('duration_s')} s, picture {packet.get('size', ['?', '?'])[0]}x{packet.get('size', ['?', '?'])[1]}, "
                  f"language {sp.get('language') or 'none heard'}.",
                  f"Speech: {sp.get('words', 0)} words, {sp.get('words_per_minute', 0)} words a minute, talking {round(100 * (sp.get('speaking_share') or 0))}% of the time, "
                  f"first word at {sp.get('first_words_at_s')} s.",
                  f"First line: \"{sp.get('first_line') or ''}\"",
                  f"Cuts: {cuts.get('count', 0)} ({cuts.get('in_first_3s', 0)} in the first 3 s); a shot lasts {cuts.get('average_shot_s')} s on average, "
                  f"the longest {cuts.get('longest_shot_s')} s. {cuts.get('note', '')}",
                  f"Cut times (s): {', '.join(str(t) for t in (cuts.get('times') or [])[:120]) or 'none'}", ""]
        frames = packet.get("frames") or []
        hook = [f for f in frames if f["t"] <= 3.0]
        rest = [f for f in frames if f["t"] > 3.0]
        lines += ["## Files", "", "- transcript.txt: what is said, with times",
                  f"- {len(frames)} frames in frames/. The hook: " + ", ".join(f"{f['file']} ({f['t']} s)" for f in hook),
                  "- The rest: " + ", ".join(f"{f['file']} ({f['t']} s)" for f in rest), ""]
    else:
        lines += ["## Files", "", "- page.txt: the text (an article or what the owner pasted). There is no video.", ""]
    return lines


def write_study_md(folder: Path, source: dict, packet: dict, playbook: list[dict]) -> None:
    lines = ["# What to study", ""] + _source_lines(source, packet)
    lines += [f"## The playbook so far ({len(playbook)} lessons)", ""]
    lines += [f"#{l['number']} [{TOPICS.get(l['topic'], 'Other')}] {l['rule']}" for l in playbook] or ["(empty: every lesson is new)"]
    (folder / "STUDY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_remake_md(folder: Path, job: dict, packet: dict) -> None:
    source, brand = job["source"], job["brand"]
    lines = ["# Make one like this", "", "The owner wants our own ad in the format of this one.", ""] + _source_lines(source, packet)
    if source.get("summary") or source.get("craft_notes"):
        lines += ["## What the earlier study found", ""]
        if source.get("summary"):
            lines.append(f"What it says: {source['summary']}")
        if source.get("craft_notes"):
            lines.append(f"How it's made: {source['craft_notes']}")
        lines.append("")
    lines += [f"## The brand: {brand.get('name')} {brand.get('handle') or ''}".rstrip(), "",
              "Its voice, rules and off-limits list (these win over the format):", "", brand.get("voice") or "(none written)", ""]
    lines += ["## The owner's video playbook (apply what fits)", ""] + (job.get("playbook") or ["(empty)"]) + [""]
    if job.get("recent"):
        lines += ["## Recent video ideas (don't repeat their angle)", ""] + [f"- {t}" for t in job["recent"]] + [""]
    (folder / "REMAKE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---- Studying it ----------------------------------------------------------------------------

def run_study(ctx: Ctx, folder: Path, label: str) -> dict:
    prompt = ("Study the source described in STUDY.md in this folder and answer with its lessons for the video "
              "playbook, following the rules you were given. Work unattended: nobody can answer questions.")
    return _run_claude(ctx, folder, prompt=prompt, rules=STUDY_RULES, schema=STUDY_SCHEMA, effort=STUDY_EFFORT,
                       name=f"Playbook study: {label}", key="lessons", log_name="claude-run.log")


def run_remake(ctx: Ctx, folder: Path, label: str) -> dict:
    prompt = ("Break down the ad described in REMAKE.md in this folder and write our own idea in its format, "
              "following the rules you were given. Work unattended: nobody can answer questions.")
    return _run_claude(ctx, folder, prompt=prompt, rules=REMAKE_RULES, schema=REMAKE_SCHEMA, effort=REMAKE_EFFORT,
                       name=f"Remake: {label}", key="idea", log_name="claude-remake.log")


def _run_claude(ctx: Ctx, folder: Path, *, prompt: str, rules: Path, schema: dict, effort: str, name: str, key: str,
                log_name: str) -> dict:
    """Headless Claude with read-only tools in the folder; returns its structured answer."""
    cmd = [ctx.claude, "-p", prompt, "--output-format", "json", "--model", STUDY_MODEL, "--effort", effort,
           "--permission-mode", "auto", "--permission-prompts", "none", "--strict-mcp-config", "--no-session-persistence",
           "--append-system-prompt-file", str(rules), "--json-schema", json.dumps(schema),
           "--name", name[:80], "--tools", "Read", "Glob"]
    proc = subprocess.Popen(cmd, cwd=str(folder), env=ctx.child_env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    try:
        out, err = proc.communicate(timeout=STUDY_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        proc.communicate()
        raise RuntimeError(f"Claude ran out of time ({STUDY_TIMEOUT_S // 60} min).")
    (folder / log_name).write_text(((out or "") + ("\n[stderr]\n" + err if err else ""))[-100_000:], encoding="utf-8")
    for line in (out or "").strip().splitlines()[::-1]:
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue
        answer = result.get("structured_output")
        if isinstance(answer, dict) and key in answer:
            return answer
        raise RuntimeError(f"Claude ended without an answer: {str(result.get('result') or '')[:300]}")
    raise RuntimeError("Claude ended without an answer.")


def _label(source: dict) -> str:
    return source.get("url") or source.get("file_name") or (source.get("body") or "text")[:40]


def _clean_old() -> None:
    cutoff = time.time() - KEEP_DAYS * 86400
    for d in STUDIES.glob("*") if STUDIES.exists() else []:
        try:
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def study_next(ctx: Ctx) -> bool:
    """One source, if any is waiting. True when there was one (studied or failed)."""
    got = ctx.engine.call("claim_source")
    source = got.get("source")
    if not source:
        return False
    sid = source["id"]
    ctx.log(f"study {sid}: {_label(source)}")
    _clean_old()
    folder = STUDIES / f"{dt.date.today():%Y-%m-%d}-{sid[:8]}"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        packet = gather(ctx, source, folder)
        if packet.get("error"):
            code = packet.get("code") or "download"
            # A network hiccup may pass; a login wall, a removed video or a 2-hour video won't.
            retry = code in ("download", "prep")
            ctx.log(f"study {sid} can't get it ({code}): {packet['error']}")
            ctx.engine.call("source_failed", source_id=sid, error=packet["error"], code=code, retryable=retry)
            return True
        write_study_md(folder, source, packet, got.get("playbook") or [])
        answer = run_study(ctx, folder, _label(source))
        text_file = folder / ("transcript.txt" if (folder / "transcript.txt").exists() else "page.txt")
        transcript = text_file.read_text(encoding="utf-8")[:100_000] if text_file.exists() else ""
        site = packet.get("site") or {}
        ctx.engine.call(
            "source_done", source_id=sid,
            title=answer.get("title") or site.get("title") or "", creator=answer.get("creator") or site.get("uploader") or "",
            summary=answer.get("summary") or "", craft_notes=answer.get("craft_notes") or "",
            duration_s=packet.get("duration_s"), language=(packet.get("speech") or {}).get("language") or "",
            transcript=transcript if source["kind"] != "text" else "", lessons=answer.get("lessons") or [],
        )
        ctx.log(f"study {sid} done: {len(answer.get('lessons') or [])} lessons")
    except Exception as e:  # noqa: BLE001 - reported back; the function retries up to 3 times
        ctx.log(f"study {sid} failed: {e}")
        try:
            ctx.engine.call("source_failed", source_id=sid, error=str(e)[:900], code="prep", retryable=True)
        except Exception as e2:  # noqa: BLE001
            ctx.log(f"couldn't report the failed study: {e2}")
    return True


# ---- Remakes --------------------------------------------------------------------------------

def study_folder(source_id: str) -> Path | None:
    """The newest folder where this source was got ready (frames, transcript), if it's still there."""
    found = [d for d in STUDIES.glob(f"*-{source_id[:8]}") if (d / "packet.json").exists()] if STUDIES.exists() else []
    for d in sorted(found, reverse=True):
        try:
            packet = json.loads((d / "packet.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not packet.get("error"):
            return d
    return None


def reference_frames(source_id: str) -> list[Path]:
    folder = study_folder(source_id)
    return sorted((folder / "frames").glob("*.png")) if folder and (folder / "frames").exists() else []


def remake_next(ctx: Ctx) -> bool:
    """One remake, if any is waiting. True when there was one (made or failed)."""
    job = ctx.engine.call("claim_remake").get("remake")
    if not job:
        return False
    source = job["source"]
    sid = source["id"]
    ctx.log(f"remake {sid}: {_label(source)}")
    try:
        folder = study_folder(sid)
        if folder:
            packet = json.loads((folder / "packet.json").read_text(encoding="utf-8"))
        else:
            folder = STUDIES / f"{dt.date.today():%Y-%m-%d}-{sid[:8]}"
            folder.mkdir(parents=True, exist_ok=True)
            packet = gather(ctx, source, folder)
        if packet.get("error"):
            code = packet.get("code") or "download"
            ctx.engine.call("remake_failed", source_id=sid, error=packet["error"], retryable=code in ("download", "prep"))
            return True
        if packet.get("kind") != "video":
            ctx.engine.call("remake_failed", source_id=sid, error="A remake needs a video; this one is a page or text.", retryable=False)
            return True
        write_remake_md(folder, job, packet)
        answer = run_remake(ctx, folder, _label(source))
        ctx.engine.call("remake_done", source_id=sid, remake=answer)
        ctx.log(f"remake {sid} done: {(answer.get('idea') or {}).get('title', '')} ({answer.get('route')})")
    except Exception as e:  # noqa: BLE001 - reported back; the function retries up to 3 times
        ctx.log(f"remake {sid} failed: {e}")
        try:
            ctx.engine.call("remake_failed", source_id=sid, error=str(e)[:900], retryable=True)
        except Exception as e2:  # noqa: BLE001
            ctx.log(f"couldn't report the failed remake: {e2}")
    return True


# ---- The skill ------------------------------------------------------------------------------

DESCRIPTION = (
    "The owner's own video-marketing playbook: numbered lessons on hooks, story, pacing, visuals, on-screen "
    "text, voice and sound, endings, captions and posting, taken from marketing videos and posts the owner sent "
    "and approved. Use it whenever planning, scripting, animating, editing or reviewing ANY video for any brand "
    "(Instagram Reels, TikToks, YouTube Shorts, ads, promo, launch and explainer films, Reelkit, HyperFrames or "
    "Remotion projects) and when writing video ideas, hooks or captions. Read it before writing the script."
)


def _src_name(s: dict) -> str:
    return (s.get("title") or (s.get("url") or "").replace("https://", "").replace("www.", "") or "a text the owner sent")[:90]


def _src_link(s: dict) -> str:
    name = _src_name(s).replace("[", "(").replace("]", ")")
    return f"[{name}]({s['url']})" if s.get("url") else name


def render(data: dict) -> dict[str, str]:
    lessons = data.get("lessons") or []
    sources = {s["id"]: s for s in data.get("sources") or []}
    used = {int(k): v for k, v in (data.get("used") or {}).items()}
    by_id = {l["id"]: l for l in lessons}
    backers: dict[str, list[str]] = {}
    folded = set()
    for l in lessons:
        if l.get("relation") == "supports" and l.get("related_id") in by_id:
            folded.add(l["id"])
            backers.setdefault(l["related_id"], []).append(l["source_id"])
    shown = [l for l in lessons if l["id"] not in folded]
    changed = max((str(l.get("decided_at") or "")[:10] for l in lessons), default="")
    source_ids = {l["source_id"] for l in lessons}

    head = [
        "---", "name: video-playbook", f"description: {json.dumps(DESCRIPTION, ensure_ascii=False)}", "---", "", "# Video playbook", "",
        (f"{len(shown)} lessons from {len(source_ids)} sources, last changed {changed}." if shown else "No lessons yet."),
        "The owner sends marketing videos and posts to the CRM's Telegram bot, the video PC studies each one, and the",
        "owner adds the lessons worth keeping. This file is written from the CRM (Content → Playbook) by",
        "`wat-framework/tools/content_studio`: don't edit it by hand, the next sync overwrites it. Change lessons in the CRM.",
        "", "## How to use it",
        "- Read all of it before you plan a video, and apply every lesson that fits this video and its format.",
        "- The owner's rules win over this playbook: the project's rules, the brand's voice and off-limits list, and",
        "  whatever the owner said about this video. Never invent a fact, number or result to follow a lesson.",
        "- \"N sources agree\" means several marketers said it. When two lessons pull different ways, prefer the one",
        "  with more sources, or the one the owner's own results back.",
        "- Take the technique, not the source's words, music or footage.",
        "- When you report on a video, name the lesson numbers you applied (\"Playbook #3, #7\").", "",
    ]
    body: list[str] = []
    if not shown:
        body += ["## Nothing here yet", "", "The owner hasn't added any lessons yet. Follow the project's own rules.", ""]
    for topic, label in TOPICS.items():
        group = [l for l in shown if l["topic"] == topic]
        if not group:
            continue
        body += [f"## {label}", ""]
        for l in group:
            ids = list(dict.fromkeys([l["source_id"], *backers.get(l["id"], [])]))
            links = [_src_link(sources[i]) for i in ids if i in sources]
            meta = [f"From {', '.join(links)}" if links else ""]
            if len(ids) > 1:
                meta.append(f"{len(ids)} sources agree")
            if used.get(l["number"]):
                meta.append(f"used in {used[l['number']]} videos")
            body.append(f"- **#{l['number']}** {l['rule']}")
            if l.get("why"):
                body.append(f"  - Why: {l['why']}")
            if l.get("example"):
                body.append(f"  - Looks like: {l['example']}")
            body.append(f"  - {' · '.join(m for m in meta if m)}")
        body.append("")
    body += ["Every source with its summary: `references/sources.md`.", ""]

    refs = ["# Where the playbook's lessons come from", ""]
    numbers: dict[str, list[int]] = {}
    for l in lessons:
        numbers.setdefault(l["source_id"], []).append(l["number"])
    for i, sid in enumerate(sorted(source_ids, key=lambda x: str(sources.get(x, {}).get("created_at") or "")), 1):
        s = sources.get(sid, {})
        bits = [s.get("creator") or "", PLATFORMS.get(s.get("platform") or "", ""), f"sent {str(s.get('created_at') or '')[:10]}"]
        refs.append(f"{i}. {_src_link(s)}: {' · '.join(b for b in bits if b)}. Lessons {', '.join(f'#{n}' for n in sorted(numbers.get(sid, [])))}.")
        if s.get("summary"):
            refs.append(f"   {s['summary']}")
    refs.append("")
    return {"SKILL.md": "\n".join(head + body), "references/sources.md": "\n".join(refs)}


def sync_playbook(ctx: Ctx) -> None:
    files = render(ctx.engine.call("playbook"))
    changed = []
    for rel, text in files.items():
        path = SKILL_DIR / rel
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        changed.append(rel)
    if changed:
        ctx.log(f"playbook skill updated: {', '.join(changed)}")
