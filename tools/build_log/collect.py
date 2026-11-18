"""Build log: tells the Mapflow work report what got built on this PC.

Every hour (Task Scheduler, see setup_schedule.ps1) it gathers:
  commits   every git repo under the home folder, only commits by this PC's git user
            (git config user.email), all branches, cherry-picks counted once; "shipped"
            when the commit is on the remote's main branch
  projects  each repo's first commit (a new project shows up in the period it started)
  systems   new tool folders (tools/*/) and workflows (workflows/*.md) in wat-framework
  skills    Claude Code skills in ~/.claude/skills and wat-framework/.claude/skills, dated
            by their folder's creation time; our own ones are marked, installed packs are
            named from the .<pack>-source.txt notes next to them
and sends it to the work-report function, which files it for the day/week/month reports
(Telegram + the CRM's Work report page). Only titles, dates and line counts leave the PC:
never code, diffs or file contents.

Only the standard library. The key is the content studio's (tools/content_studio/.env):
  CONTENT_ENGINE_URL     .../functions/v1/content-engine  (work-report is next to it)
  CONTENT_WORKER_SECRET  the PC's key
Optional: BUILD_LOG_URL to point somewhere else.

Usage:
  python collect.py              gather and send (what the scheduled task runs)
  python collect.py --dry-run    gather only; writes .tmp/build_log/last_payload.json
  python collect.py --days 400   look further back (the first run does this by itself)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WAT = HERE.parent.parent
HOME = Path.home()
STATE_DIR = WAT / ".tmp" / "build_log"
STATE = STATE_DIR / "state.json"
LOG = STATE_DIR / "collect.log"
CONFIG = HERE / "projects.json"
LOCAL_CONFIG = HERE / "projects.local.json"   # git-ignored: client names, extra roots
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

DEFAULT_DAYS = 45
BACKFILL_DAYS = 400
RESEND_AFTER_H = 12      # an unchanged payload is still sent this often
BATCH = 1000


# ---- Small helpers ---------------------------------------------------------------------------

def log(message: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {message}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if sys.stdout and not sys.stdout.closed:
        try:
            print(line)
        except Exception:
            pass


def git(repo: Path, *args: str, timeout: int = 60) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, creationflags=NO_WINDOW,
    )
    return result.stdout if result.returncode == 0 else ""


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if LOCAL_CONFIG.exists():
        local = json.loads(LOCAL_CONFIG.read_text(encoding="utf-8"))
        for key, value in local.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key] = {**config[key], **value}
            elif isinstance(value, list) and isinstance(config.get(key), list):
                config[key] = config[key] + value
            else:
                config[key] = value
    return config


def load_env() -> dict:
    env: dict[str, str] = {}
    path = WAT / "tools" / "content_studio" / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("CONTENT_ENGINE_URL", "CONTENT_WORKER_SECRET", "BUILD_LOG_URL"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()


def created_at(path: Path) -> float:
    st = path.stat()
    # Windows keeps the creation time (Python 3.12+: st_birthtime; before that st_ctime is it).
    return getattr(st, "st_birthtime", None) or st.st_ctime


def title_case(name: str) -> str:
    words = re.split(r"[-_\s]+", name.strip())
    return " ".join(w[:1].upper() + w[1:] for w in words if w)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(HOME.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---- Repos and commits -----------------------------------------------------------------------

def find_repos(config: dict) -> list[Path]:
    skip = set(config.get("skip_dirs", []))
    skip_repos = set(config.get("skip_repos", []))
    max_depth = int(config.get("max_depth", 4))
    roots = [Path(os.path.expandvars(os.path.expanduser(r))) for r in config.get("roots", [str(HOME)])]
    found: list[Path] = []
    seen: set[str] = set()

    def walk(folder: Path, depth: int) -> None:
        try:
            entries = list(os.scandir(folder))
        except OSError:
            return
        names = {e.name for e in entries}
        # A worktree or submodule has a .git file; only real repos (a .git folder) count.
        if ".git" in names and (folder / ".git").is_dir():
            key = rel(folder)
            if key not in seen and key not in skip_repos:
                seen.add(key)
                found.append(folder)
        if depth >= max_depth:
            return
        for e in entries:
            if not e.is_dir(follow_symlinks=False) or e.name in skip or e.name == ".git":
                continue
            # Windows' old "My Documents" style junctions and node_modules links.
            if getattr(e, "is_junction", lambda: False)():
                continue
            if e.name.startswith(".") and e.name not in config.get("dot_dirs_to_scan", []):
                continue
            walk(Path(e.path), depth + 1)

    for root in roots:
        if root.exists():
            walk(root, 0)
    return found


GENERIC_REPO_NAMES = {"site", "app", "web", "website", "frontend", "repo", "code", "src"}


def product_of(repo: Path, config: dict) -> str:
    names = config.get("product_names", {})
    key = rel(repo)
    if key in names:
        return names[key]
    if repo.name in names:
        return names[repo.name]
    folder = repo.parent if repo.name.lower() in GENERIC_REPO_NAMES else repo
    return names.get(folder.name) or title_case(folder.name)


def my_emails(repos: list[Path]) -> set[str]:
    emails = set()
    for scope in (["config", "--global", "user.email"],):
        out = git(WAT, *scope).strip()
        if out:
            emails.add(out.lower())
    for repo in repos:
        out = git(repo, "config", "user.email").strip()
        if out:
            emails.add(out.lower())
    return emails


def main_ref(repo: Path) -> tuple[str | None, bool]:
    """The branch that counts as shipped: the remote's default, else a local main."""
    head = git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
    if head:
        return head.replace("refs/remotes/", ""), True
    for ref, remote in (("origin/main", True), ("origin/master", True), ("main", False), ("master", False)):
        if git(repo, "rev-parse", "--verify", "--quiet", ref).strip():
            return ref, remote
    return None, False


STAT = re.compile(r"(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?")


def repo_commits(repo: Path, emails: set[str], since_days: int) -> list[dict]:
    authors = [f"--author={re.escape(e)}" for e in sorted(emails)]
    if not authors:
        return []
    out = git(repo, "log", "--all", "--no-merges", f"--since={since_days} days ago", *authors,
              "--format=%x1e%H%x1f%aI%x1f%ae%x1f%s%x1f%b%x1f", "--shortstat", timeout=120)
    commits = []
    for chunk in out.split("\x1e"):
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 6:
            continue
        sha, when, email, subject, body, rest = parts[0].strip(), parts[1], parts[2].lower(), parts[3].strip(), parts[4], parts[5]
        if email not in emails or not subject:
            continue
        m = STAT.search(rest)
        commits.append({
            "sha": sha, "when": when, "subject": subject,
            # Only the first lines of the message, and never trailers like Co-Authored-By.
            "body": "\n".join(l for l in body.strip().splitlines()[:6] if not re.match(r"^[A-Za-z-]+: ", l)).strip(),
            "files": int(m.group(1)) if m else 0,
            "added": int(m.group(2) or 0) if m else 0,
            "removed": int(m.group(3) or 0) if m else 0,
        })
    if not commits:
        return commits
    ref, remote = main_ref(repo)
    shipped = set(git(repo, "rev-list", ref, f"--since={since_days + 30} days ago", timeout=120).split()) if ref else set()
    for c in commits:
        c["shipped"] = c["sha"] in shipped
        c["remote"] = remote
    return commits


def first_commit(repo: Path) -> str | None:
    out = git(repo, "log", "--all", "--max-parents=0", "--format=%aI").split()
    return min(out) if out else None


def collect_commits(repos: list[Path], config: dict, days: int, emails: set[str]) -> list[dict]:
    """One row per change. A cherry-pick (same author time and subject) is one change,
    shipped if any copy is on main; the same commit in two clones is one change too."""
    by_key: dict[str, dict] = {}
    for repo in repos:
        product = product_of(repo, config)
        for c in repo_commits(repo, emails, days):
            key = hashlib.sha1(f"{c['when']}\n{c['subject']}".encode("utf-8")).hexdigest()[:20]
            row = by_key.get(key)
            if row:
                row["meta"]["shipped"] = row["meta"]["shipped"] or c["shipped"]
                continue
            by_key[key] = {
                "kind": "commit",
                "ref": f"c:{key}",
                "project": product,
                "title": c["subject"][:300],
                "detail": c["body"][:1500] or None,
                "happened_at": c["when"],
                "meta": {"repo": rel(repo), "shipped": c["shipped"], "remote": c["remote"],
                         "files": c["files"], "added": c["added"], "removed": c["removed"]},
            }
    return list(by_key.values())


def collect_projects(repos: list[Path], config: dict, emails: set[str]) -> list[dict]:
    rows: dict[str, dict] = {}
    for repo in repos:
        # Only projects this PC's user worked on (not cloned tools like open-seo).
        if not git(repo, "log", "--all", "-1", "--format=%H", *[f"--author={re.escape(e)}" for e in sorted(emails)]).strip():
            continue
        when = first_commit(repo)
        if not when:
            continue
        product = product_of(repo, config)
        if product in rows and rows[product]["happened_at"] <= when:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", product.lower()).strip("-")
        rows[product] = {"kind": "project", "ref": f"p:{slug}", "project": product, "title": product,
                         "detail": None, "happened_at": when, "meta": {"repo": rel(repo)}}
    return list(rows.values())


# ---- Tools and workflows ---------------------------------------------------------------------

def first_added(path: Path) -> str | None:
    out = git(WAT, "log", "--diff-filter=A", "--format=%aI", "--", str(path.relative_to(WAT)).replace("\\", "/")).split()
    return min(out) if out else None


def clean_title(title: str | None) -> str | None:
    if not title:
        return None
    t = re.sub(r"^(workflow|tool|sop)\s*:\s*", "", title.strip(), flags=re.I)
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t) or t
    return t.strip() or None


def plain(text: str) -> str:
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def heading_and_line(text: str) -> tuple[str | None, str | None]:
    lines = text.splitlines()
    title = None
    start = 0
    for i, raw in enumerate(lines):
        if raw.strip().startswith("# "):
            title = raw.strip()[2:].strip()
            start = i + 1
            break
    paragraph: list[str] = []
    for raw in lines[start:] + [""]:
        line = raw.strip()
        if not line:
            if paragraph:
                break
            continue
        if not paragraph and line.startswith(("#", "|", "- ", "* ", ">", "```", "<", "---")):
            continue
        paragraph.append(line)
    about = re.sub(r"^(objective|goal|purpose|what it does)\s*:\s*", "", plain(" ".join(paragraph)), flags=re.I).strip()
    return clean_title(title), (about[:300] or None)


def collect_systems(config: dict) -> list[dict]:
    rows = []
    skip = set(config.get("skip_tools", []))
    for folder in sorted((WAT / "tools").iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "_")) or folder.name in skip:
            continue
        title, about = None, None
        for doc in ("README.md", "SKILL.md"):
            if (folder / doc).exists():
                title, about = heading_and_line((folder / doc).read_text(encoding="utf-8", errors="replace"))
                break
        if not about:
            for py in sorted(folder.glob("*.py")):
                m = re.match(r'\s*(?:"""|\'\'\')\s*(.+)', py.read_text(encoding="utf-8", errors="replace"))
                if m:
                    about = m.group(1).strip()
                    break
        when = first_added(folder) or iso(created_at(folder))
        rows.append({"kind": "system", "ref": f"s:tools/{folder.name}", "project": "WAT framework",
                     "title": (title or title_case(folder.name))[:120], "detail": (about or "")[:300] or None,
                     "happened_at": when, "meta": {"type": "tool", "path": f"tools/{folder.name}"}})
    for md in sorted((WAT / "workflows").glob("*.md")):
        title, about = heading_and_line(md.read_text(encoding="utf-8", errors="replace"))
        when = first_added(md) or iso(created_at(md))
        rows.append({"kind": "system", "ref": f"s:workflows/{md.name}", "project": "WAT framework",
                     "title": (title or title_case(md.stem))[:120], "detail": (about or "")[:300] or None,
                     "happened_at": when, "meta": {"type": "workflow", "path": f"workflows/{md.name}"}})
    return rows


# ---- Skills ----------------------------------------------------------------------------------

def skill_description(skill_md: Path) -> str | None:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        if line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-", ""):
                parts = []
                for nxt in lines[i + 1:]:
                    if nxt.startswith((" ", "\t")):
                        parts.append(nxt.strip())
                    else:
                        break
                value = " ".join(parts)
            value = value.strip().strip('"').strip("'")
            return value[:300] or None
    return None


def skill_packs(skills_dir: Path) -> list[dict]:
    """The notes left next to installed packs (.marketingskills-source.txt …): which
    skills each one brought, by the names it lists, ig-* style patterns, or skills
    created within a minute of the note."""
    packs = []
    for note in sorted(skills_dir.glob(".*-source.txt")):
        label = note.name[1:-len("-source.txt")]
        text = note.read_text(encoding="utf-8", errors="replace")
        packs.append({"label": label, "text": text, "at": note.stat().st_mtime,
                      "patterns": re.findall(r"\b([a-z0-9]+-)\*", text)})
    return packs


def pack_of(name: str, made_ts: float, packs: list[dict]) -> str | None:
    for pack in packs:
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", pack["text"]):
            return pack["label"]
        if any(name.startswith(prefix) for prefix in pack["patterns"]):
            return pack["label"]
    for pack in packs:
        if abs(pack["at"] - made_ts) <= 60:
            return pack["label"]
    return None


def collect_skills(config: dict) -> list[dict]:
    own_names = set(config.get("own_skills", []))
    dirs = [(WAT / ".claude" / "skills", True), (HOME / ".claude" / "skills", False)]
    rows: dict[str, dict] = {}
    for skills_dir, own_dir in dirs:
        if not skills_dir.exists():
            continue
        packs = [] if own_dir else skill_packs(skills_dir)
        for entry in sorted(skills_dir.iterdir()):
            if entry.name.startswith(".") or not entry.is_dir():
                continue
            if not ((entry / "SKILL.md").exists() or (entry / "skill.md").exists()):
                continue
            name = entry.name
            if name in rows:
                continue  # a link to one already listed (israel-digital-compliance)
            target = entry.resolve()
            own = own_dir or name in own_names or str(target).lower().startswith(str((WAT / ".claude").resolve()).lower())
            made = created_at(target)
            rows[name] = {
                "kind": "skill", "ref": f"k:{name}", "project": None, "title": name,
                "detail": skill_description(target / "SKILL.md"), "happened_at": iso(made),
                "meta": {"own": bool(own), "source": None if own else pack_of(name, made, packs)},
            }
    return list(rows.values())


# ---- Sending ---------------------------------------------------------------------------------

def endpoint(env: dict) -> str | None:
    if env.get("BUILD_LOG_URL"):
        return env["BUILD_LOG_URL"]
    url = env.get("CONTENT_ENGINE_URL", "")
    return re.sub(r"/content-engine/?$", "/work-report", url) if url.endswith(("content-engine", "content-engine/")) else None


def send(url: str, secret: str, items: list[dict]) -> dict:
    total = {"saved": 0, "skipped": 0}
    for i in range(0, len(items), BATCH):
        body = json.dumps({"action": "builds", "items": items[i:i + BATCH]}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json", "x-content-worker": secret,
        })
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    answer = json.loads(resp.read().decode("utf-8") or "{}")
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")[:300]
                if e.code < 500 or attempt == 2:
                    raise RuntimeError(f"work-report answered {e.code}: {detail}") from None
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 2:
                    raise RuntimeError(f"couldn't reach work-report: {e}") from None
            time.sleep(5 * (attempt + 1))
        total["saved"] += int(answer.get("saved", 0))
        total["skipped"] += int(answer.get("skipped", 0))
    return total


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="gather only, send nothing")
    parser.add_argument("--days", type=int, default=None, help="how far back to read commits")
    parser.add_argument("--force", action="store_true", help="send even if nothing changed")
    args = parser.parse_args()

    state = read_state()
    days = args.days or (DEFAULT_DAYS if state.get("backfilled") else BACKFILL_DAYS)
    config = load_config()
    started = time.time()
    repos = find_repos(config)
    emails = my_emails(repos)
    items = collect_commits(repos, config, days, emails) + collect_projects(repos, config, emails) \
        + collect_systems(config) + collect_skills(config)
    items.sort(key=lambda r: (r["kind"], r["ref"]))
    digest = hashlib.sha256(json.dumps(items, sort_keys=True).encode("utf-8")).hexdigest()
    counts = {k: sum(1 for r in items if r["kind"] == k) for k in ("commit", "project", "system", "skill")}
    summary = f"{len(repos)} repos, {counts} in {time.time() - started:.1f}s (last {days} days)"

    if args.dry_run:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / "last_payload.json").write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
        log(f"dry run: {summary}; payload in .tmp/build_log/last_payload.json")
        return 0

    fresh = state.get("digest") == digest and time.time() - state.get("sent_at", 0) < RESEND_AFTER_H * 3600
    if fresh and not args.force:
        log(f"nothing new: {summary}")
        return 0
    env = load_env()
    url, secret = endpoint(env), env.get("CONTENT_WORKER_SECRET")
    if not url or not secret:
        log("missing CONTENT_ENGINE_URL / CONTENT_WORKER_SECRET in tools/content_studio/.env "
            "(run tools/content_studio/connect_worker.py once)")
        return 1
    try:
        result = send(url, secret, items)
    except Exception as e:  # noqa: BLE001 - one line in the log, try again next hour
        log(f"send failed: {e}")
        return 1
    state.update({"digest": digest, "sent_at": time.time(), "backfilled": True})
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state), encoding="utf-8")
    log(f"sent: {summary}; saved {result['saved']}, skipped {result['skipped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
