"""
Runs the Ready missions from the Claude Missions board in Notion.

Picks up missions set to Ready, and new rows with no Status once they haven't been
edited for 10 minutes. Draft means "leave it". For each (High priority first, oldest first):
  1. marks it Running and reads the page body (images/files are downloaded),
  2. gives it its own git worktree on a mission/... branch (the normal checkout
     is never touched), or a scratch folder for missions without a project,
  3. runs Claude Code headless there: auto permission mode, nothing that would
     prompt is allowed, no MCP connectors, and git push blocked through git config,
  4. writes Claude's report back into the page and sets Needs review,
     Needs info or Failed.

A run that gets cut off (lost connection, Claude server error, time limit, PC off,
crash) puts the mission back to Ready so the next run carries on from the work in
its worktree; after 3 cut-offs in a row it's marked Failed. A result that can't be
written to Notion is kept in .tmp/notion_missions/pending/ and sent on the next run.

Usage:
    python tools/notion_missions/run_missions.py [--max 3] [--timeout-min 75] [--dry-run]

Scheduled hourly by the WAT-NotionMissions task (see setup_schedule.ps1).
Logs: .tmp/notion_missions/runner.log, raw Claude output in .tmp/notion_missions/logs/.
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import live
from board import (DONE, FAILED, MEMORY_DIR, NEEDS_INFO, NEEDS_REVIEW, NEW_PROJECT, NO_PROJECT,
                   P_BRANCH, P_LAST_RUN, P_MISSION, P_PRIORITY, P_PROJECT, P_RESULT, P_STATUS,
                   PRIORITY_RANK, READY, RUNNING, STATE_DIR, WORKSPACE, find_database, is_trusted,
                   list_projects, load_config, page_text, prop_text, queue_order, short_id, slug,
                   sync_project_options)
from notion_api import ROOT, Notion, NotionError, block, markdown_to_blocks, rich_text

log = logging.getLogger("missions")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["done", "needs_info", "failed"]},
        "summary": {"type": "string", "description": "One short line for the board"},
        "report": {"type": "string", "description": "Markdown report for the mission page"},
        "questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "summary", "report", "questions"],
}

# Command patterns a mission may never run, on top of the push block and auto mode's own checks.
DENIED_COMMANDS = ["git push*", "git remote set-url*", "gh *", "vercel *", "npx vercel*",
                   "supabase db push*", "supabase functions deploy*",
                   "npx supabase db push*", "npx supabase functions deploy*"]
DENIED_TOOLS = [f"{shell}({c})" for shell in ("Bash", "PowerShell") for c in DENIED_COMMANDS]

MODEL = "claude-opus-5-5"  # user's choice (2026-10-19): Opus 5.5 at high effort for everything
EFFORT = "high"

USAGE_LIMIT_HINTS = ("usage limit", "rate limit", "rate_limit", "limit reached")
TRANSIENT_HINTS = ("can't reach the api", "enotfound", "econnreset", "econnrefused", "etimedout",
                   "socket hang up", "network", "connection error", "overloaded", "internal server error")
WAITING = "Waiting: Claude usage limit reached, will retry on a later run."
RETRY_NOTE = "Paused: {why}. Claude carries on from the work so far on the next run."
MAX_ATTEMPTS = 3      # cut-offs in a row before a mission is marked Failed
RUN_BUDGET_MIN = 120  # don't start another mission after this long (the task allows 4 h)
SETTLE_MINUTES = 10  # a row with no Status runs once nobody has edited it for this long
INLINE_PROMPT_LIMIT = 15000  # longer missions are read from the saved file instead


# --- helpers -------------------------------------------------------------------

def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()[:500]}")
    return result.stdout.strip()


def is_repo_root(path: Path) -> bool:
    return (path / ".git").exists()


def default_branch(repo: Path) -> str:
    for name in ("main", "master"):
        if git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}", check=False):
            return name
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def find_claude() -> str:
    override = os.environ.get("CLAUDE_BIN")
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
    """Environment for the Claude run: subscription auth only, git push disabled."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "NOTION_TOKEN", "CLAUDECODE")
           and not k.startswith("CLAUDE_CODE_")}
    prefixes = ["https://", "http://", "git@", "ssh://", "git://", "file://"]
    env["GIT_CONFIG_COUNT"] = str(len(prefixes))
    for i, prefix in enumerate(prefixes):
        env[f"GIT_CONFIG_KEY_{i}"] = "url.push-disabled-by-mission-runner://blocked/.pushInsteadOf"
        env[f"GIT_CONFIG_VALUE_{i}"] = prefix
    return env


def pid_alive(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


class RunLock:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        if self.path.exists():
            try:
                pid = int(json.loads(self.path.read_text())["pid"])
            except (ValueError, KeyError, json.JSONDecodeError):
                pid = 0
            if pid and pid_alive(pid):
                raise SystemExit(f"Another run is in progress (pid {pid}).")
        self.path.write_text(json.dumps({"pid": os.getpid(), "started": now_iso()}))
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


# --- workspace for one mission ---------------------------------------------------

class Workspace:
    """Where a mission runs: a worktree on its own branch, a scratch folder, or a plain folder."""

    def __init__(self, cwd: Path, kind: str, repo: Path | None = None, branch: str = "", base: str = "",
                 root: Path | None = None):
        self.cwd, self.kind, self.repo, self.branch, self.base = cwd, kind, repo, branch, base
        self.root = root or cwd  # worktree root; differs from cwd when the project is a repo subfolder

    def describe(self) -> str:
        if self.kind == "worktree":
            where = (f"in {self.cwd}, inside a git worktree at {self.root}" if self.cwd != self.root
                     else f"in a git worktree at {self.cwd}")
            return (f"You are {where}, on branch {self.branch}, made from "
                    f"{self.base} of the repo at {self.repo}. Make every change and commit here. The "
                    f"normal checkout at {self.repo} may hold my work in progress or other sessions' "
                    f"work: you may read from it (node_modules, .env files, local check scripts) but "
                    f"never edit, commit, switch branches or stash there. A fresh worktree has no "
                    f"node_modules: install dependencies in the worktree if you need to build or test.")
        if self.kind == "scratch":
            return (f"This mission has no project. Work in the scratch folder {self.cwd} and put any "
                    f"files you produce there. The report is what I read, so put the answer itself in it.")
        if self.kind == "new":
            return (f"This mission starts a new project. You are at the workspace root {self.cwd}. "
                    f"Create the project in its own folder under the right category (websites/, saas/ "
                    f"or internal/, see CLAUDE.md), give it its own git repo and commit there. Don't "
                    f"commit to the workspace repo itself.")
        return (f"You are in {self.cwd}. It is not a git repository, so there is no branch to keep your "
                f"work apart. Change only what the mission needs and list every file you changed in the report.")


def prepare_workspace(page: dict, project: str, projects: dict[str, Path], title: str) -> Workspace:
    short = short_id(page["id"])
    if project == NO_PROJECT:
        folder = STATE_DIR / "scratch" / short
        folder.mkdir(parents=True, exist_ok=True)
        return Workspace(folder, "scratch")
    if project == NEW_PROJECT:
        return Workspace(ROOT, "new")
    path = projects[project]
    found = repo_for(path)
    if not found:
        return Workspace(path, "plain")
    repo, rel = found

    worktree = STATE_DIR / "wt" / short
    branch = prop_text(page, P_BRANCH)
    base = default_branch(repo)
    if worktree.exists() and (worktree / ".git").exists():
        current = git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
        return Workspace(worktree / rel, "worktree", repo, current, base, worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "prune", check=False)
    if branch and git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False):
        git(repo, "worktree", "add", str(worktree), branch)
        return Workspace(worktree / rel, "worktree", repo, branch, base, worktree)
    name = slug(title) or "task"
    branch = f"mission/{datetime.date.today():%Y%m%d}-{short}-{name}"[:90].rstrip("-")
    git(repo, "worktree", "add", "-b", branch, str(worktree), base)
    return Workspace(worktree / rel, "worktree", repo, branch, base, worktree)


def repo_for(path: Path) -> tuple[Path, Path] | None:
    """(repo root, project path inside it) when the project is a repo or tracked by one, else None."""
    if is_repo_root(path):
        return path, Path(".")
    top = git(path, "rev-parse", "--show-toplevel", check=False)
    if not top:
        return None
    repo = Path(top).resolve()
    rel = path.resolve().relative_to(repo)
    # Must exist on the branch the worktree is made from, not just in the index
    # (a staged-but-uncommitted move would give a worktree without the folder).
    in_base = git(repo, "ls-tree", "--name-only", default_branch(repo), "--", rel.as_posix(), check=False)
    return (repo, rel) if in_base else None


# --- the Claude run ----------------------------------------------------------------

def build_rules(ws: Workspace, attachments: Path) -> str:
    return f"""You are running unattended as my mission agent, started by tools/notion_missions/run_missions.py in my WAT workspace. Nobody is watching this session and you can't ask me anything while it runs.

Where you work:
- {ws.describe()}
- Notes from my earlier sessions are in {MEMORY_DIR / 'MEMORY.md'}. Read the index and the entries that concern this project before you start.
- Images and files attached to the mission are in {attachments} (when there are any).

Hard limits. I do these myself after I review your work:
- Never push, merge into main, deploy, release, apply migrations to a live database, publish, or change anything on a live site or service. git push is disabled in this session.
- Never send emails, messages or notifications to anyone, and never run anything that spends paid credits (paid AI, image or video APIs, ads, domains).
- Never print secret values or copy them into files, commits or your report.
- Don't delete files or data outside your own work folder.
If the mission can't be finished without one of these, do everything up to that point and say exactly what's left for me.

How to work:
- Do the mission fully, the way you would in a normal session with me: read the code first, follow the project's CLAUDE.md, and verify the result with the build, tests and checks that exist. For UI changes, check them in a browser with Playwright when you can.
- Commit as you go, at each step that works, with clear commit messages, so a run that gets cut off loses nothing. Leave nothing uncommitted at the end.
- If your work folder already has uncommitted changes, they come from an earlier attempt at this mission that was cut off (lost connection or time limit). Check them and carry on from there instead of starting over.
- If the mission is unclear or needs a decision only I can make, don't guess on things that matter. Do the safe parts, then finish with status needs_info and your questions.
- Where my instructions (CLAUDE.md) say to ask me something with AskUserQuestion, put it in your questions instead.
- Write the summary and report in the language the mission is written in.

Your final answer is structured:
- status: done (finished and verified), needs_info (waiting for my answer) or failed (couldn't do it).
- summary: one short line for the board.
- report: Markdown for the mission page. Cover what you changed, how you verified it, anything left for me (for example what to release and how), and how to look at the result.
- questions: only with needs_info, one question per item."""


def build_prompt(title: str, project: str, priority: str, body: str, saved_at: Path) -> str:
    """The full mission is saved to `saved_at`; the prompt carries it inline unless it's very long."""
    page = (f"Mission: {title}\nProject: {project}\nPriority: {priority or 'Normal'}\n\n"
            f"----- mission page -----\n{body or '(the page is empty, so the title is the whole mission)'}\n"
            f"----- end of mission page -----\n")
    saved_at.parent.mkdir(parents=True, exist_ok=True)
    saved_at.write_text(page, encoding="utf-8")
    intro = ("Carry out this mission from my Notion board \"Claude Missions\". If the page holds earlier "
             "reports from you and my answers, continue from there (your earlier commits are on the branch).\n\n")
    if len(page) <= INLINE_PROMPT_LIMIT:
        return intro + page
    return intro + f"The mission page is long, so it's saved in {saved_at}. Read all of it before you start."


def run_claude(cmd: list[str], cwd: Path, env: dict, timeout_s: int) -> tuple[dict | None, str]:
    """Returns (parsed JSON result or None, raw stdout+stderr)."""
    proc = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                            creationflags=NO_WINDOW)
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=NO_WINDOW)
        else:
            proc.kill()
        out, err = proc.communicate()
        return {"_timeout": True}, (out or "") + (err or "")
    raw = (out or "") + ("\n[stderr]\n" + err if err else "")
    for text in (out or "").strip().splitlines()[::-1] or [""]:
        try:
            return json.loads(text), raw
        except json.JSONDecodeError:
            continue
    return None, raw


def claude_command(prompt: str, rules: str, title: str, ws: Workspace, attachments: Path) -> list[str]:
    cmd = [find_claude(), "-p", prompt,
           "--output-format", "json",
           "--model", MODEL,
           "--effort", EFFORT,
           "--permission-mode", "auto",
           "--permission-prompts", "none",
           "--strict-mcp-config",
           "--append-system-prompt", rules,
           "--json-schema", json.dumps(RESULT_SCHEMA),
           "--name", f"Mission: {title}"[:80],
           "--disallowedTools", *DENIED_TOOLS]
    extra_dirs = [MEMORY_DIR, attachments] + ([ws.repo] if ws.kind == "worktree" else [])
    cmd += ["--add-dir", *[str(d) for d in extra_dirs if d and Path(d).exists()]]
    return cmd


def parse_outcome(result: dict | None, raw: str) -> dict:
    """Normalises Claude's output to {status, summary, report, questions, session_id, denials, limit}."""
    if result is None:
        return {"status": "failed", "summary": "Claude's output couldn't be read",
                "report": "The run ended without a readable result. Last output:\n```\n" + raw[-1500:] + "\n```",
                "questions": []}
    if result.get("_timeout"):
        return {"status": "retry", "why": "it ran into the time limit", "summary": "", "report": "", "questions": []}
    text = str(result.get("result") or "")
    if result.get("is_error") or result.get("subtype") not in (None, "success"):
        low, code = text.lower(), result.get("api_error_status")
        if code == 429 or any(h in low for h in USAGE_LIMIT_HINTS):
            return {"status": "limit", "summary": "", "report": "", "questions": []}
        if (isinstance(code, int) and code >= 500) or any(h in low for h in TRANSIENT_HINTS):
            return {"status": "retry", "why": "the connection to Claude dropped", "stop_run": True,
                    "summary": "", "report": f"```\n{text[:1500]}\n```", "questions": []}
        return {"status": "failed", "summary": "Claude stopped with an error",
                "report": f"```\n{text[:1500] or result.get('subtype')}\n```", "questions": [],
                "session_id": result.get("session_id")}
    data = result.get("structured_output")
    if not isinstance(data, dict):
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            data = {"status": "done", "summary": text.strip().splitlines()[0][:200] if text.strip() else "Finished",
                    "report": text, "questions": []}
    data.setdefault("questions", [])
    data["session_id"] = result.get("session_id")
    data["denials"] = result.get("permission_denials") or []
    return data


# --- reporting back to Notion ----------------------------------------------------------

def git_summary(ws: Workspace) -> tuple[list[str], list[str]]:
    if ws.kind != "worktree":
        return [], []
    # Only the mission's own commits: a mission may rebase onto origin/main, which can hold
    # other sessions' pushed work that the local main doesn't have yet.
    upstream = f"origin/{ws.base}"
    exclude = [ws.base] + ([upstream] if git(ws.cwd, "rev-parse", "--verify", "--quiet",
                                              f"refs/remotes/{upstream}", check=False) else [])
    commits = git(ws.cwd, "log", "--format=%h %s", "HEAD", "--not", *exclude,
                  check=False).splitlines() if ws.base else []
    dirty = git(ws.cwd, "status", "--porcelain", check=False).splitlines()
    return commits, dirty


def report_blocks(outcome: dict, ws: Workspace, commits: list[str], dirty: list[str]) -> list[dict]:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [block("divider"), block("heading_2", f"🤖 Claude's report · {stamp}")]
    blocks += markdown_to_blocks(outcome.get("report") or outcome.get("summary") or "")
    if outcome.get("questions"):
        blocks.append(block("heading_3", "Questions for you"))
        blocks += [block("numbered_list_item", q) for q in outcome["questions"]]
        blocks.append(block("paragraph", "Write your answers under this, then set Status back to Ready."))
    details = []
    if ws.kind == "worktree":
        details.append(f"Branch `{ws.branch}` in {ws.repo.name}, {len(commits)} commit(s) on top of `{ws.base}`")
        details += [f"`{c}`" for c in commits[:15]]
        details.append(f"Worktree folder: {ws.cwd}")
        if dirty:
            details.append(f"⚠ {len(dirty)} uncommitted change(s) left in the worktree")
    elif ws.kind == "scratch":
        details.append(f"Files (if any): {ws.cwd}")
    if outcome.get("denials"):
        names = sorted({d.get("tool_name", "?") for d in outcome["denials"]})
        details.append(f"Blocked actions during the run: {len(outcome['denials'])} ({', '.join(names)})")
    if outcome.get("session_id"):
        details.append(f"To continue this session yourself: open {ws.cwd} and run "
                       f"`claude --resume {outcome['session_id']}`")
    if details:
        blocks.append(block("toggle", "Run details", children=[block("bulleted_list_item", d) for d in details]))
    return blocks


def status_props(status: str, summary: str, branch: str = "") -> dict:
    props = {P_STATUS: {"select": {"name": status}}, P_RESULT: {"rich_text": rich_text(summary[:1900])}}
    if branch:
        props[P_BRANCH] = {"rich_text": rich_text(branch)}
    return props


def finish(notion: Notion, page_id: str, status: str, summary: str, branch: str = "") -> None:
    notion.update_page(page_id, status_props(status, summary, branch))


def _send(notion: Notion, item: dict) -> None:
    if not item["appended"] and item["blocks"]:
        notion.append(item["page_id"], item["blocks"])
        item["appended"] = True  # so a retry after a failed status update doesn't post the report twice
    notion.update_page(item["page_id"], item["props"])


def deliver(notion: Notion, page_id: str, blocks: list[dict], props: dict) -> bool:
    """Writes a finished mission's report and status; if Notion can't be reached, keeps them for the next run."""
    item = {"page_id": page_id, "blocks": blocks, "props": props, "appended": False}
    try:
        _send(notion, item)
        return True
    except NotionError as exc:
        pending = STATE_DIR / "pending" / f"{short_id(page_id)}.json"
        pending.parent.mkdir(parents=True, exist_ok=True)
        pending.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
        log.error("  couldn't write the result to Notion (%s); saved, it's sent on the next run", exc)
        return False


def flush_pending(notion: Notion) -> None:
    """Sends results that an earlier run couldn't write to Notion. Raises if Notion is still unreachable."""
    folder = STATE_DIR / "pending"
    for path in sorted(folder.glob("*.json")) if folder.exists() else []:
        item = json.loads(path.read_text(encoding="utf-8"))
        try:
            _send(notion, item)
        except NotionError:
            path.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
            raise
        path.unlink()
        log.info("Sent the saved result of mission %s to Notion", short_id(item["page_id"]))


def _attempts() -> dict:
    try:
        return json.loads((STATE_DIR / "attempts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def bump_attempts(short: str) -> int:
    counts = _attempts()
    counts[short] = counts.get(short, 0) + 1
    (STATE_DIR / "attempts.json").write_text(json.dumps(counts), encoding="utf-8")
    return counts[short]


def clear_attempts(short: str) -> None:
    counts = _attempts()
    if counts.pop(short, None) is not None:
        (STATE_DIR / "attempts.json").write_text(json.dumps(counts), encoding="utf-8")


# --- main flow ------------------------------------------------------------------------------

def classify(prompt: str, options: list[str]) -> str:
    """Asks Claude to pick one of `options` (no tools, no session kept). Returns '' on any failure."""
    schema = {"type": "object", "properties": {"project": {"type": "string", "enum": options}},
              "required": ["project"]}
    cmd = [find_claude(), "-p", prompt, "--output-format", "json", "--model", MODEL, "--effort", EFFORT,
           "--tools", "",
           "--strict-mcp-config", "--permission-prompts", "none", "--no-session-persistence",
           "--json-schema", json.dumps(schema)]
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    result, _raw = run_claude(cmd, STATE_DIR, child_env(), 180)
    answer = (result or {}).get("structured_output")
    if not isinstance(answer, dict):
        try:
            answer = json.loads((result or {}).get("result") or "")
        except (ValueError, TypeError):
            answer = {}
    return answer.get("project", "") if isinstance(answer, dict) else ""


def guess_project(notion: Notion, cfg: dict, title: str, body: str, projects: dict[str, Path]) -> str:
    """For a mission without a Project: which project is it about? '' when it's unclear."""
    names = sorted(projects, key=str.lower)
    recent = {}
    for row in notion.query_database(cfg["database_id"]):
        name = prop_text(row, P_PROJECT)
        if name in projects:
            recent[name] = recent.get(name, 0) + 1
    memory = MEMORY_DIR / "MEMORY.md"
    notes = memory.read_text(encoding="utf-8", errors="replace")[:40000] if memory.exists() else ""
    prompt = (f"Which of my projects is this mission about? Answer with exactly one project name from the "
              f"list, \"{NO_PROJECT}\" if it's research or writing that needs no code, or \"unclear\" if you "
              f"can't tell with confidence.\n\nMission: {title}\n{body[:4000]}\n\n"
              f"My projects: {', '.join(names)}\n"
              f"Other missions on the board are in: {', '.join(f'{k} ({v})' for k, v in recent.items()) or 'none yet'}\n\n"
              f"Notes about my projects (my session memory index):\n{notes}")
    choice = classify(prompt, names + [NO_PROJECT, "unclear"])
    return choice if choice in projects or choice == NO_PROJECT else ""


def run_one(notion: Notion, cfg: dict, page: dict, projects: dict[str, Path], args) -> str:
    """Runs one mission. Returns 'done', 'needs_info', 'failed', 'retry' or 'skipped', or
    'stop' when the rest of this run should wait (usage limit, lost connection, Notion down)."""
    pid = page["id"]
    title = prop_text(page, P_MISSION) or "(untitled mission)"
    project = prop_text(page, P_PROJECT)
    priority = prop_text(page, P_PRIORITY)
    log.info("Mission %s: %s [%s]", short_id(pid), title, project or "no project set")

    # Only missions last edited by you, or by this integration on your behalf (only your
    # own tools hold its token), may run. Anyone else's edit blocks the mission.
    problem = None
    body = None
    attachments = STATE_DIR / "attachments" / short_id(pid)
    if not is_trusted(page, cfg):
        problem = ("Not run: someone other than you edited this mission last. "
                   "Check the page, then set Ready again yourself.")
    elif not project and args.dry_run:
        log.info("  no Project chosen: Claude would pick one")
    elif not project:
        body = page_text(notion, pid, attachments)
        try:
            project = guess_project(notion, cfg, title, body, projects)
        except NotionError:
            raise
        except Exception as exc:
            log.warning("  couldn't pick a project: %s", exc)
            project = ""
        if project:
            notion.update_page(pid, {P_PROJECT: {"select": {"name": project}}})
            log.info("  no Project chosen, Claude picked: %s", project)
        else:
            problem = ("Not run: Claude couldn't tell which project this is for. "
                       "Pick it in the Project column, then set Ready again.")
    elif project not in projects and project not in (NO_PROJECT, NEW_PROJECT):
        problem = f"Not run: no project folder called '{project}' in the workspace."

    if args.dry_run:
        where = problem or f"would run in {projects.get(project, project or 'the project Claude picks')}"
        log.info("  dry run: %s", where)
        return "skipped"
    if problem:
        finish(notion, pid, NEEDS_INFO, problem)
        return "skipped"

    started = time.time()
    notion.update_page(pid, {P_STATUS: {"select": {"name": RUNNING}},
                             P_RESULT: {"rich_text": rich_text(live.WORKING_PREFIX + "starting")},
                             P_LAST_RUN: {"date": {"start": now_iso()}}})
    safe_refresh(notion, cfg, {pid: started})
    try:
        if body is None:
            body = page_text(notion, pid, attachments)
        ws = prepare_workspace(page, project, projects, title)
        if ws.branch:
            notion.update_page(pid, {P_BRANCH: {"rich_text": rich_text(ws.branch)}})
        log.info("  working in %s (%s%s)", ws.cwd, ws.kind, f", branch {ws.branch}" if ws.branch else "")

        prompt = build_prompt(title, project, priority, body, attachments / "mission.md")
        cmd = claude_command(prompt, build_rules(ws, attachments), title, ws, attachments)
        with live.Ticker(lambda: live.refresh(notion, cfg, {pid: started}), log=log):
            result, raw = run_claude(cmd, ws.cwd, child_env(), args.timeout_min * 60)
        logs = STATE_DIR / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{short_id(pid)}.json").write_text(raw, encoding="utf-8")
        outcome = parse_outcome(result, raw)
    except NotionError:
        raise  # Notion unreachable: the card stays Running and the next run takes it up again
    except Exception as exc:  # anything else before or around the run: report it on the card
        log.exception("  mission crashed")
        finish(notion, pid, FAILED, f"Runner error: {exc}"[:1900])
        return "failed"

    short = short_id(pid)
    if outcome["status"] == "limit":
        finish(notion, pid, READY, WAITING, ws.branch)
        log.info("  -> usage limit reached, back to Ready")
        return "stop"
    if outcome["status"] == "retry":
        tries = bump_attempts(short)
        if tries < MAX_ATTEMPTS:
            finish(notion, pid, READY, RETRY_NOTE.format(why=outcome["why"]), ws.branch)
            log.info("  -> cut off (%s), continues next run (try %d of %d)", outcome["why"], tries, MAX_ATTEMPTS)
            return "stop" if outcome.get("stop_run") else "retry"
        outcome = {**outcome, "status": "failed", "summary": f"Gave up after {tries} tries: {outcome['why']}",
                   "report": f"The run was cut off {tries} times in a row ({outcome['why']}). The work so far "
                             f"is in the worktree. Set Ready to try again.\n{outcome.get('report', '')}"}
    clear_attempts(short)

    commits, dirty = git_summary(ws)
    status = {"done": NEEDS_REVIEW, "needs_info": NEEDS_INFO}.get(outcome["status"], FAILED)
    sent = deliver(notion, pid, report_blocks(outcome, ws, commits, dirty),
                   status_props(status, outcome.get("summary") or status, ws.branch))
    log.info("  -> %s: %s", status, outcome.get("summary"))
    return outcome["status"] if sent else "stop"


def pick_missions(notion: Notion, db_id: str) -> list[dict]:
    """Missions to run: Ready ones, plus new rows without a Status once they've settled.
    Ordered High priority first, then oldest."""
    rows = notion.query_database(db_id, {"or": [
        {"property": P_STATUS, "select": {"equals": READY}},
        {"property": P_STATUS, "select": {"is_empty": True}},
    ]})
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=SETTLE_MINUTES)
    picked = []
    for page in rows:
        if not prop_text(page, P_MISSION) and not notion.children(page["id"]):
            continue  # an empty row (no name, no text) isn't a mission
        edited = datetime.datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00"))
        if prop_text(page, P_STATUS) == READY or edited <= cutoff:
            picked.append(page)
        else:
            log.info("New mission still being written, next run: %s", prop_text(page, P_MISSION) or short_id(page["id"]))
    return queue_order(picked)


def accept_new_rows(notion: Notion, cfg: dict, picked: list[dict]) -> None:
    """New rows (no Status) that made it into the queue get Status Ready, so the board shows them waiting."""
    for page in picked:
        if not prop_text(page, P_STATUS) and is_trusted(page, cfg):
            notion.update_page(page["id"], {P_STATUS: {"select": {"name": READY}}})


def safe_refresh(notion: Notion, cfg: dict, running: dict | None = None) -> None:
    try:
        live.refresh(notion, cfg, running)
    except Exception as exc:  # the live view must never stop the missions
        log.warning("Live status update failed: %s", exc)


def recover_interrupted(notion: Notion, db_id: str) -> None:
    """We hold the run lock, so anything still Running is left over from a run that died.
    It goes back to Ready to carry on, unless it has been cut off too often."""
    for page in notion.query_database(db_id, {"property": P_STATUS, "select": {"equals": RUNNING}}):
        short = short_id(page["id"])
        tries = bump_attempts(short)
        if tries < MAX_ATTEMPTS:
            finish(notion, page["id"], READY, RETRY_NOTE.format(
                why="the previous run stopped before it finished (PC off, lost connection or a crash)"))
            log.info("Mission %s was cut off last time, it carries on (try %d of %d)", short, tries, MAX_ATTEMPTS)
        else:
            finish(notion, page["id"], FAILED, f"Gave up after {tries} interrupted runs. Work so far "
                                               f"is on the branch. Set Ready to try again.")
            clear_attempts(short)


def clean_done_worktrees(notion: Notion, db_id: str) -> None:
    """Removes clean worktrees of missions you marked Done. The branches stay."""
    for page in notion.query_database(db_id, {"property": P_STATUS, "select": {"equals": DONE}}):
        worktree = STATE_DIR / "wt" / short_id(page["id"])
        if (worktree / ".git").exists() and not git(worktree, "status", "--porcelain", check=False):
            common = Path(git(worktree, "rev-parse", "--git-common-dir", check=False))
            repo = common.parent if common.is_absolute() else (worktree / common).resolve().parent
            git(repo, "worktree", "remove", str(worktree), check=False)
            log.info("Removed worktree of done mission %s", short_id(page["id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=3, help="Most missions to run in one go")
    parser.add_argument("--timeout-min", type=int, default=75, help="Time limit per mission")
    parser.add_argument("--dry-run", action="store_true", help="List what would run, change nothing")
    parser.add_argument("--status", action="store_true", help="Only refresh the live view in Notion")
    args = parser.parse_args()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [logging.FileHandler(STATE_DIR / "runner.log", encoding="utf-8")]
    if sys.stdout:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=handlers)

    cfg = load_config()
    notion = Notion()
    db_id = find_database(notion, cfg)
    if args.status:
        live.refresh(notion, cfg)
        return

    started = time.monotonic()
    with RunLock(STATE_DIR / "run.lock"):
        if not args.dry_run:
            flush_pending(notion)  # before recovery, so those missions get their real result
            sync_project_options(notion, cfg)
            recover_interrupted(notion, db_id)
            clean_done_worktrees(notion, db_id)
        ready = pick_missions(notion, db_id)
        log.info("%d mission(s) ready", len(ready))
        if not args.dry_run:
            accept_new_rows(notion, cfg, ready)
            safe_refresh(notion, cfg)
        projects = list_projects(cfg)
        for page in ready[:args.max]:
            if (time.monotonic() - started) / 60 > RUN_BUDGET_MIN:
                log.info("This run has used its time, the rest wait for the next run")
                break
            try:
                outcome = run_one(notion, cfg, page, projects, args)
            except NotionError as exc:
                log.error("Notion unreachable (%s), stopping; the next run carries on", exc)
                break
            except Exception:
                log.exception("Runner error on mission %s, stopping; the next run carries on", short_id(page["id"]))
                break
            if outcome == "stop":
                log.info("Stopping this run (usage limit, lost connection or Notion unreachable)")
                break
            if not args.dry_run:
                safe_refresh(notion, cfg)
        if not args.dry_run:
            safe_refresh(notion, cfg)  # nothing running any more


if __name__ == "__main__":
    try:
        main()
    except NotionError as exc:
        logging.getLogger("missions").error("%s", exc)
        sys.exit(str(exc))
    except SystemExit:
        raise
    except Exception:  # under pythonw there's no console, so make sure crashes reach the log
        logging.getLogger("missions").exception("Runner crashed")
        sys.exit(1)
