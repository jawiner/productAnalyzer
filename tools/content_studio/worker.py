"""Content studio worker: makes the videos the owner approved on Telegram.

Runs on the video PC from Task Scheduler every 10 minutes (see setup_schedule.ps1):
  1. asks the content-engine function for the next approved idea (or change request)
  2. builds a Reelkit project for it (a copy of the template, or the previous version's
     project for a change), writes BRIEF.md
  3. runs Claude Code headless in that folder to script, voice, animate, render and check it
  4. uploads final.mp4 (posting), review.mp4 (Telegram) and cover.jpg, and reports back;
     the function sends the video to Telegram for approval.

Only the standard library. Config in tools/content_studio/.env (never committed):
  CONTENT_ENGINE_URL=https://<project>.supabase.co/functions/v1/content-engine
  CONTENT_WORKER_SECRET=<the content_worker_secret row>
  CONTENT_VIDEO_ROOT=C:/Users/97254/lifemaxing-independent/marketing/video/daily   (optional)

Usage:
  python worker.py --once        one pass (what the scheduled task runs)
  python worker.py --check       check the config and the connection, take no job
  python worker.py --playbook    only write the video playbook skill from the CRM

Each pass also keeps the video playbook in step (playbook.py): it writes the lessons the owner
added into ~/.claude/skills/video-playbook, and when no video is waiting it studies the next
marketing video, post or text the owner sent to learn from.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

import playbook

HERE = Path(__file__).resolve().parent
STATE = HERE.parent.parent / ".tmp" / "content_studio"
LOCK = STATE / "worker.lock"
LOG = STATE / "worker.log"
TEMPLATE = HERE / "template"
RULES = HERE / "rules.md"
DEFAULT_ROOT = Path("C:/Users/97254/lifemaxing-independent/marketing/video/daily")
MODEL = "claude-opus-5-5"
EFFORT = "high"
CLAUDE_TIMEOUT_S = 150 * 60
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "error", "playbook_used"],
    "properties": {
        "status": {"type": "string", "enum": ["done", "failed"]},
        "summary": {"type": "string"},
        "error": {"type": "string"},
        # The video-playbook lesson numbers this video applied (the CRM counts them per lesson).
        "playbook_used": {"type": "array", "items": {"type": "integer"}},
    },
}


# ---- Small helpers ---------------------------------------------------------------------------

def log(message: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {message}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if sys.stdout and not sys.stdout.closed:
        try:
            print(line)
        except Exception:
            pass


def load_env() -> dict:
    env = {}
    path = HERE / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for key in ("CONTENT_ENGINE_URL", "CONTENT_WORKER_SECRET", "CONTENT_VIDEO_ROOT", "CLAUDE_BIN"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


class Engine:
    """Calls to the content-engine function. The secret only travels in a header."""

    def __init__(self, url: str, secret: str):
        self.url, self.secret = url, secret

    def call(self, action: str, **body) -> dict:
        data = json.dumps({"action": action, **body}).encode()
        req = urllib.request.Request(self.url, data=data, method="POST", headers={
            "Content-Type": "application/json", "x-content-worker": self.secret,
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"content-engine {action}: HTTP {e.code} {detail}") from None

    def download(self, action: str, path: Path, **body) -> None:
        """An action that answers with a file (a video the owner sent on Telegram)."""
        data = json.dumps({"action": action, **body}).encode()
        req = urllib.request.Request(self.url, data=data, method="POST", headers={
            "Content-Type": "application/json", "x-content-worker": self.secret,
        })
        try:
            with urllib.request.urlopen(req, timeout=300) as r, path.open("wb") as f:
                shutil.copyfileobj(r, f)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"content-engine {action}: HTTP {e.code} {detail}") from None

    def progress(self, video_id: str, note: str) -> None:
        try:
            self.call("progress", video_id=video_id, note=note)
        except Exception as e:  # progress is best effort
            log(f"progress failed: {e}")


def put_file(url: str, path: Path, content_type: str) -> None:
    req = urllib.request.Request(url, data=path.read_bytes(), method="PUT", headers={
        "Content-Type": content_type, "x-upsert": "true",
    })
    with urllib.request.urlopen(req, timeout=300) as r:
        if r.status >= 300:
            raise RuntimeError(f"upload of {path.name} failed: HTTP {r.status}")


def pid_alive(pid: int) -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                             creationflags=NO_WINDOW).stdout
        return str(pid) in out
    except Exception:
        return False


def take_lock() -> bool:
    STATE.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip() or 0)
        except ValueError:
            pid = 0
        if pid and pid_alive(pid):
            return False
    LOCK.write_text(str(os.getpid()))
    return True


def find_claude(env: dict) -> str:
    override = env.get("CLAUDE_BIN")
    if override and Path(override).exists():
        return override
    found = shutil.which("claude")
    if found:
        return found
    candidates = sorted(Path.home().glob(".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude.exe"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    candidates += [Path.home() / ".local" / "bin" / "claude.exe"]
    for c in candidates:
        if c.exists():
            return str(c)
    raise RuntimeError("Can't find the claude CLI (not on PATH, not in the VS Code extension).")


def child_env() -> dict:
    """Subscription auth only, and git push disabled for the run."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CONTENT_WORKER_SECRET", "CLAUDECODE")
           and not k.startswith("CLAUDE_CODE_")}
    prefixes = ["https://", "http://", "git@", "ssh://", "git://", "file://"]
    env["GIT_CONFIG_COUNT"] = str(len(prefixes))
    for i, prefix in enumerate(prefixes):
        env[f"GIT_CONFIG_KEY_{i}"] = "url.push-disabled-by-content-studio://blocked/.pushInsteadOf"
        env[f"GIT_CONFIG_VALUE_{i}"] = prefix
    env["PYTHONUTF8"] = "1"
    return env


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40].strip("-") or "video"


def ffprobe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type",
                          "-of", "json", str(path)], capture_output=True, text=True, creationflags=NO_WINDOW)
    data = json.loads(out.stdout or "{}")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    return {"duration": float(data.get("format", {}).get("duration") or 0), "width": video.get("width"),
            "height": video.get("height"), "audio": audio}


# ---- The project ----------------------------------------------------------------------------

def prepare_project(job: dict, root: Path) -> Path:
    video, idea = job["video"], job["idea"]
    previous = job.get("previous") or {}
    prev_dir = Path(previous["project_dir"]) if previous.get("project_dir") else None
    if video.get("version", 1) > 1 and prev_dir and prev_dir.exists():
        project = prev_dir
        # Keep what the last version delivered, then work on the same project.
        keep = project / "backup" / f"v{previous.get('version', video['version'] - 1)}"
        keep.mkdir(parents=True, exist_ok=True)
        for name in ("final.mp4", "review.mp4", "cover.jpg", "caption.txt"):
            src = project / "out" / name
            if src.exists():
                shutil.copy2(src, keep / name)
                src.unlink()
        return project
    project = root / f"{dt.date.today():%Y-%m-%d}-{slug(idea['title'])}"
    n = 2
    while project.exists():
        project = root / f"{dt.date.today():%Y-%m-%d}-{slug(idea['title'])}-{n}"
        n += 1
    shutil.copytree(TEMPLATE, project)
    cfg = project / "reelkit.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    data["name"] = project.name
    cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return project


def write_brief(project: Path, job: dict) -> None:
    video, idea, brand = job["video"], job["idea"], job["brand"]
    previous = job.get("previous") or {}
    parts = [
        f"# Video brief: {idea['title']}",
        "",
        f"Brand: **{brand['name']}** {brand.get('handle') or ''}  ",
        f"Version: {video.get('version', 1)}  ",
        f"Video id: {video['id']}",
        "",
    ]
    if video.get("change_request"):
        parts += [
            "## THIS IS A CHANGE REQUEST",
            "",
            "The owner watched the previous version and asked for this change. Edit the existing project in this",
            "folder. Change only what they asked for and keep everything else as it was (use `reelkit render",
            "--allow <frames>` if the change is local). The previous files are in `backup/`.",
            "",
            f"> {video['change_request']}",
            "",
            f"Previous caption:\n\n```\n{previous.get('caption') or ''}\n```",
            "",
        ]
    parts += [
        "## The idea the owner approved",
        "",
        "```json",
        json.dumps({k: idea.get(k) for k in ("title", "pillar", "hook_line", "on_screen_hook", "concept", "beats", "facts", "caption_seed", "why")},
                   ensure_ascii=False, indent=2),
        "```",
        "",
        "## The brand (voice, rules, off-limits)",
        "",
        brand.get("voice") or "",
        "",
    ]
    if job.get("learnings"):
        parts += ["## What the numbers taught us (apply it)", ""] + [f"- {t}" for t in job["learnings"]] + [""]
    if idea.get("source_id"):
        parts += remake_brief(project, idea, job.get("reference") or {})
    (project / "BRIEF.md").write_text("\n".join(parts), encoding="utf-8")


def remake_brief(project: Path, idea: dict, ref: dict) -> list[str]:
    """A remake: the owner liked an ad and approved our version of it. Its format goes in the brief,
    and its frames into reference/remake/ so the run can match layout, text size and rhythm."""
    frames = playbook.reference_frames(idea["source_id"])
    target = project / "reference" / "remake"
    if frames and not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        for f in frames:
            shutil.copy2(f, target / f.name)
    bp = idea.get("blueprint") or {}
    lines = [
        "## THIS IS A REMAKE",
        "",
        "The owner liked an ad and approved our version of it (the idea above). Build it in the reference's",
        "FORMAT: its beat order and timing, its kind of hook, its text style and size, its rhythm of cuts. Each",
        "beat's `mirrors` says which of their beats it takes the job of. Keep it ours: never their words, footage,",
        "music, logo, product, characters or people. The brand's rules and the hard rules still win.",
        "",
        f"Reference: {ref.get('title') or ''} {ref.get('url') or ''}".rstrip(),
        f"How it's made: {ref.get('craft_notes')}" if ref.get("craft_notes") else None,
        f"The format: {bp.get('format') or ''}",
        f"Its hook: {bp.get('hook') or ''}",
        "",
        "Their beats:",
    ]
    for b in bp.get("their_beats") or []:
        text = f" Text: {b.get('text_on_screen')}." if b.get("text_on_screen") else ""
        lines.append(f"- {b.get('start_s')}-{b.get('end_s')} s, {b.get('job')}: {b.get('visual')}.{text} Audio: {b.get('audio')}")
    keeps = bp.get("keep") or []
    if keeps:
        video = playbook.reference_video(idea["source_id"])
        lines += ["", "KEEP AS IS (the owner asked): these stretches of the reference go into our video exactly as they are,",
                  "with their own sound, where the reference has them (usually first); our beats follow them. Credit the",
                  "original creator in caption.txt (\"🎥 Clip: @handle\" or \"Clip via <site>\").", ""]
        for n, k in enumerate(keeps, 1):
            clip_path = target / f"keep-{n}.mp4"
            ok = clip_path.exists() or (video is not None and playbook.cut_clip(video, float(k["start_s"]), float(k["end_s"]), clip_path))
            lines.append(f"- `reference/remake/keep-{n}.mp4`: {k['start_s']}-{k['end_s']} s, {k.get('what')}"
                         + ("" if ok else " (MISSING: the reference video is no longer on this PC; fail the job and say so)"))
    ai_clips = sorted((playbook.AI_FOOTAGE / str(idea.get("id") or "")).glob("*.mp4")) if idea.get("id") else []
    if ai_clips:
        ai_dir = target / "ai"
        ai_dir.mkdir(parents=True, exist_ok=True)
        for f in ai_clips:
            if not (ai_dir / f.name).exists():
                shutil.copy2(f, ai_dir / f.name)
        lines += ["", "AI FOOTAGE (made with the owner's credits; use it, never regenerate it): the presenter shots are in",
                  "`reference/remake/ai/`. Use their picture AND their own voice for the presenter's lines: don't record",
                  "those lines with Gemini, and time captions to a faster-whisper transcript of the clip's audio. Cut away",
                  "from the presenter to the app, Steppy and the cards where the beats say, with the presenter's voice",
                  "carrying on underneath. Lines the clip doesn't contain get the usual Gemini voice.", ""]
        lines += [f"- `reference/remake/ai/{f.name}`" for f in ai_clips]
    lines += ["", f"Frames of the reference: `reference/remake/` ({len(frames)} stills, named by time: t000150.png = 1.5 s). "
              "Look at them before you plan." if frames else "(The reference's frames are no longer on this PC; work from the beats.)", ""]
    return [l for l in lines if l is not None]


def run_claude(project: Path, env: dict, engine: Engine, video_id: str) -> tuple[dict | None, str]:
    prompt = ("Make the video described in BRIEF.md in this folder, following the rules you were given. "
              "Work unattended: nobody can answer questions. When the four deliverables are in out/ and pass "
              "their checks, answer with status done; if you can't make it work, answer failed with the reason.")
    cmd = [find_claude(env), "-p", prompt,
           "--output-format", "json",
           "--model", MODEL,
           "--effort", EFFORT,
           "--permission-mode", "auto",
           "--permission-prompts", "none",
           "--strict-mcp-config",
           "--append-system-prompt-file", str(RULES),
           "--json-schema", json.dumps(RESULT_SCHEMA),
           "--name", f"Content studio: {project.name}"[:80],
           "--disallowedTools", "AskUserQuestion", "WebFetch", "WebSearch",
           "--add-dir", str(Path.home() / ".claude" / "skills"), str(HERE)]
    log(f"claude starts in {project}")
    proc = subprocess.Popen(cmd, cwd=str(project), env=child_env(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    started = time.time()
    stop = threading.Event()

    def beat():
        while not stop.wait(120):
            minutes = int((time.time() - started) / 60)
            engine.progress(video_id, f"Claude is making it ({minutes} min)")

    threading.Thread(target=beat, daemon=True).start()
    try:
        out, err = proc.communicate(timeout=CLAUDE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        out, err = proc.communicate()
        stop.set()
        return {"_timeout": True}, (out or "") + (err or "")
    stop.set()
    raw = (out or "") + ("\n[stderr]\n" + err if err else "")
    (project / "out").mkdir(exist_ok=True)
    (project / "out" / "claude-run.log").write_text(raw[-200_000:], encoding="utf-8")
    for line in (out or "").strip().splitlines()[::-1] or [""]:
        try:
            return json.loads(line), raw
        except json.JSONDecodeError:
            continue
    return None, raw


def outcome(result: dict | None) -> dict:
    if not result:
        return {"status": "failed", "error": "Claude ended without a result.", "summary": ""}
    if result.get("_timeout"):
        return {"status": "failed", "error": f"Claude ran out of time ({CLAUDE_TIMEOUT_S // 60} min).", "summary": ""}
    structured = result.get("structured_output") or {}
    if isinstance(structured, dict) and structured.get("status"):
        return structured
    text = str(result.get("result") or "")
    if result.get("is_error"):
        return {"status": "failed", "error": text[:500] or "Claude stopped with an error.", "summary": ""}
    return {"status": "done" if "done" in text.lower() else "failed", "summary": text[:1000], "error": "" if "done" in text.lower() else text[:500]}


def check_deliverables(project: Path) -> tuple[dict, list[str]]:
    out = project / "out"
    problems = []
    for name in ("final.mp4", "review.mp4", "caption.txt"):
        if not (out / name).exists():
            problems.append(f"out/{name} is missing")
    info = {}
    if (out / "final.mp4").exists():
        info = ffprobe(out / "final.mp4")
        if (info.get("width"), info.get("height")) != (1080, 1920):
            problems.append(f"final.mp4 is {info.get('width')}x{info.get('height')}, not 1080x1920")
        if not info.get("audio"):
            problems.append("final.mp4 has no sound")
        if not 5 <= info.get("duration", 0) <= 90:
            problems.append(f"final.mp4 is {info.get('duration', 0):.1f} s long")
    caption = (out / "caption.txt").read_text(encoding="utf-8").strip() if (out / "caption.txt").exists() else ""
    if (out / "caption.txt").exists() and not caption:
        problems.append("caption.txt is empty")
    if re.search(r"lifemaxing", caption, re.I):
        problems.append('the caption says "Lifemaxing" (the brand is LifeMaxer)')
    return {"duration_s": round(info.get("duration", 0), 2), "caption": caption}, problems


# ---- One pass -----------------------------------------------------------------------------

def playbook_ctx(env: dict, engine: Engine) -> playbook.Ctx:
    return playbook.Ctx(engine, log, find_claude(env), child_env())


def run_once(env: dict) -> int:
    engine = Engine(env["CONTENT_ENGINE_URL"], env["CONTENT_WORKER_SECRET"])
    try:
        playbook.sync_playbook(playbook_ctx(env, engine))
    except Exception as e:  # the skill catches up on the next pass
        log(f"playbook sync failed: {e}")
    job = engine.call("claim").get("job")
    if not job:
        # Nothing to make: a remake the owner asked for first, then the next thing to learn from.
        try:
            if playbook.remake_next(playbook_ctx(env, engine)):
                return 0
        except Exception as e:  # e.g. the function is older than this worker; videos still work
            log(f"remake skipped: {e}")
        try:
            studied = playbook.study_next(playbook_ctx(env, engine))
        except Exception as e:
            log(f"playbook study skipped: {e}")
            studied = False
        if studied:
            # A /remake link has just been studied: its remake can go now, in the same pass.
            try:
                playbook.remake_next(playbook_ctx(env, engine))
            except Exception as e:
                log(f"remake skipped: {e}")
            try:
                playbook.sync_playbook(playbook_ctx(env, engine))
            except Exception as e:
                log(f"playbook sync failed: {e}")
        return 0
    video = job["video"]
    log(f"job {video['id']} v{video.get('version', 1)}: {job['idea']['title']}")
    root = Path(env.get("CONTENT_VIDEO_ROOT") or DEFAULT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    project = None
    try:
        project = prepare_project(job, root)
        write_brief(project, job)
        engine.progress(video["id"], "Starting")
        result, raw = run_claude(project, env, engine, video["id"])
        res = outcome(result)
        if res.get("status") != "done":
            raise RuntimeError(res.get("error") or "Claude didn't finish the video.")
        meta, problems = check_deliverables(project)
        if problems:
            raise RuntimeError("; ".join(problems))
        engine.progress(video["id"], "Uploading")
        urls = engine.call("upload_urls", video_id=video["id"])
        put_file(urls["final.mp4"]["url"], project / "out" / "final.mp4", "video/mp4")
        put_file(urls["review.mp4"]["url"], project / "out" / "review.mp4", "video/mp4")
        has_cover = (project / "out" / "cover.jpg").exists()
        if has_cover:
            put_file(urls["cover.jpg"]["url"], project / "out" / "cover.jpg", "image/jpeg")
        used = sorted({int(n) for n in (res.get("playbook_used") or []) if str(n).lstrip("-").isdigit() and int(n) > 0})
        engine.call("done", video_id=video["id"], caption=meta["caption"], duration_s=meta["duration_s"],
                    project_dir=str(project), has_cover=has_cover,
                    report={"summary": res.get("summary", "")[:2000], "playbook_used": used})
        log(f"job {video['id']} done ({meta['duration_s']} s)")
    except Exception as e:
        message = str(e)[:900]
        log(f"job {video['id']} failed: {message}\n{traceback.format_exc()[-1500:]}")
        try:
            engine.call("failed", video_id=video["id"], error=message, project_dir=str(project) if project else None)
        except Exception as e2:
            log(f"couldn't report the failure: {e2}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--playbook", action="store_true")
    args = ap.parse_args()
    env = load_env()
    missing = [k for k in ("CONTENT_ENGINE_URL", "CONTENT_WORKER_SECRET") if not env.get(k)]
    if missing:
        log(f"missing in tools/content_studio/.env: {', '.join(missing)}")
        return 2
    if args.check:
        engine = Engine(env["CONTENT_ENGINE_URL"], env["CONTENT_WORKER_SECRET"])
        try:
            engine.call("progress", video_id="00000000-0000-0000-0000-000000000000", note="check")
        except RuntimeError as e:
            # A made-up video id answers 404 only after the secret was accepted.
            ok = "HTTP 404" in str(e)
            log("connection OK (the function accepted the worker key)" if ok else f"connection FAILED: {e}")
            if not ok:
                return 1
        log(f"claude: {find_claude(env)}")
        log(f"template: {'OK' if (TEMPLATE / 'reelkit.json').exists() else 'MISSING'}")
        log(f"speech venv (study): {'OK' if playbook.SPEECH_PY.exists() else 'MISSING'}")
        # The video bot: the function points its webhook at itself (the token never leaves it).
        try:
            bot = engine.call("bot_setup")
            if not bot.get("configured"):
                log("video bot: not set up (no CONTENT_BOT_TOKEN secret); content goes through the lead bot")
            elif bot.get("username"):
                log(f"video bot: @{bot['username']}, webhook {'OK' if bot.get('ok') else 'NOT set'}"
                    + (f", last error: {bot['last_error']}" if bot.get("last_error") else ""))
            else:
                log(f"video bot: {bot.get('error') or 'not reachable'}")
        except Exception as e:  # noqa: BLE001
            log(f"video bot check failed: {e}")
        return 0
    if args.playbook:
        playbook.sync_playbook(playbook_ctx(env, Engine(env["CONTENT_ENGINE_URL"], env["CONTENT_WORKER_SECRET"])))
        log(f"playbook: {playbook.SKILL_DIR / 'SKILL.md'}")
        return 0
    if not take_lock():
        return 0
    try:
        return run_once(env)
    finally:
        try:
            LOCK.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    sys.exit(main())
