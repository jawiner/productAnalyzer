"""
Offline end-to-end test of the mission runner: fake Notion board, scratch git repo,
stub Claude. Touches nothing real and starts no agent.

    python tools/notion_missions/test_offline.py
"""
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

TOOL = Path(__file__).resolve().parent
HERE = TOOL.parent.parent / ".tmp" / "notion_missions_test"
sys.path.insert(0, str(TOOL))

import board  # noqa: E402
import notion_api  # noqa: E402
import run_missions as rm  # noqa: E402
import live  # noqa: E402

live.save_config = lambda cfg: None  # never touch the real board.json

WORK = HERE / "work"
def _force_remove(func, path, _exc):
    os.chmod(path, 0o700)  # git object files are read-only on Windows
    func(path)


if WORK.exists():
    shutil.rmtree(WORK, onerror=_force_remove)
WORK.mkdir(parents=True)
STATE = WORK / "state"
board.STATE_DIR = STATE
rm.STATE_DIR = STATE
TRANSCRIPTS = WORK / "claude-projects"  # stands in for ~/.claude/projects
TRANSCRIPTS.mkdir()
live.PROJECTS_DIR = TRANSCRIPTS

# --- scratch project repo -------------------------------------------------------
REPO = WORK / "demo-app"
REPO.mkdir()
def g(*a, cwd=REPO):
    return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True).stdout.strip()
g("init", "-q", "-b", "main")
g("config", "user.email", "t@t"); g("config", "user.name", "t")
(REPO / "app.txt").write_text("v1\n")
(REPO / "site").mkdir()
(REPO / "site" / "index.html").write_text("<p>site</p>\n")  # project tracked as a repo subfolder
(REPO / ".gitignore").write_text("ignored-proj/\n")
(REPO / "ignored-proj").mkdir()
(REPO / "ignored-proj" / "x.txt").write_text("not tracked\n")  # folder inside a repo but not part of it
g("add", "."); g("commit", "-q", "-m", "init")
g("remote", "add", "origin", "https://github.com/example/nothing.git")
(REPO / "wip.txt").write_text("user work in progress\n")  # must stay untouched

OWNER, BOT, STRANGER = "owner-1", "bot-1", "someone-else"


def NOW_Z():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
cfg = {"database_id": "db-1", "parent_page_id": "parent-1", "owner_ids": [OWNER], "bot_id": BOT,
       "extra_projects": {"demo-app": str(REPO), "demo-site": str(REPO / "site"),
                          "demo-ignored": str(REPO / "ignored-proj")}}


# --- fake Notion ------------------------------------------------------------------
def stored(prop):
    if "select" in prop:
        return {"type": "select", "select": prop["select"]}
    if "rich_text" in prop:
        return {"type": "rich_text", "rich_text": [{"plain_text": t["text"]["content"]} for t in prop["rich_text"]]}
    if "title" in prop:
        return {"type": "title", "title": [{"plain_text": t["text"]["content"]} for t in prop["title"]]}
    if "date" in prop:
        return {"type": "date", "date": prop["date"]}
    raise ValueError(prop)


class FakeNotion:
    def __init__(self):
        self.pages, self.blocks, self.options = {}, {}, ["demo-app"]
        self.deleted, self.next_id = set(), 0
        # the board's own page: how-to, tip, then the database itself
        self.blocks["parent-1"] = [para("How this board works", "how-1"), para("Tip", "tip-1"),
                                   {"id": "db-block", "type": "child_database", "has_children": False,
                                    "child_database": {"title": "Missions"}}]

    def get_page(self, pid):
        return json.loads(json.dumps(self.pages[pid]))

    def update_block(self, bid, body):
        for b in self.blocks["parent-1"]:
            if b["id"] == bid and bid not in self.deleted:
                kind = next(iter(body))
                b[kind] = json.loads(json.dumps(body[kind]))
                for t in b[kind].get("rich_text", []):
                    t["plain_text"] = t["text"]["content"]
                return b
        raise notion_api.NotionError("PATCH block -> 400 validation_error: archived or missing")

    def block_text(self, bid):
        b = next(b for b in self.blocks["parent-1"] if b["id"] == bid)
        return "".join(t["plain_text"] for t in b[b["type"]]["rich_text"])

    def add(self, pid, title, status, project="", priority="", editor=OWNER, created="2026-10-19T08:00:00Z", body=None,
            edited="2026-10-19T08:00:00.000Z"):
        props = {"Mission": stored({"title": notion_api.rich_text(title)}),
                 "Status": {"type": "select", "select": {"name": status} if status else None},
                 "Project": {"type": "select", "select": {"name": project} if project else None},
                 "Priority": {"type": "select", "select": {"name": priority} if priority else None},
                 "Result": stored({"rich_text": []}), "Branch": stored({"rich_text": []})}
        self.pages[pid] = {"id": pid, "properties": props, "last_edited_by": {"id": editor}, "created_time": created,
                           "last_edited_time": edited}
        self.blocks[pid] = body or []

    def get_database(self, db):
        return {"properties": {"Project": {"select": {"options": [{"name": n} for n in self.options]}}}}

    def update_database(self, db, body):
        self.options = [o["name"] for o in body["properties"]["Project"]["select"]["options"]]

    def query_database(self, db, filter=None, sorts=None):
        conds = (filter["or"] if "or" in filter else [filter]) if filter else []

        def match(p):
            if not conds:
                return True
            s = board.prop_text(p, "Status")
            return any(s == c["select"]["equals"] if "equals" in c["select"] else s == "" for c in conds)
        return [json.loads(json.dumps(p)) for p in self.pages.values() if match(p)]

    def update_page(self, pid, props):
        if self.fail_next_update:
            self.fail_next_update -= 1
            raise notion_api.NotionError("Can't reach Notion (Timeout)")
        for k, v in props.items():
            self.pages[pid]["properties"][k] = stored(v)
        self.pages[pid]["last_edited_by"] = {"id": BOT}
        self.pages[pid]["last_edited_time"] = NOW_Z()

    fail_append = 0       # next N append calls raise (Notion unreachable)
    fail_next_update = 0  # next N update_page calls raise

    def append(self, pid, blocks, after=None):
        if self.fail_append:
            self.fail_append -= 1
            raise notion_api.NotionError("Can't reach Notion (ConnectionError)")
        assert all("type" in b for b in blocks)
        # Notion returns appended blocks with ids and plain_text on every rich-text part
        stored_blocks = json.loads(json.dumps(blocks))
        for b in stored_blocks:
            self.next_id += 1
            b["id"], b["has_children"] = f"blk-{self.next_id}", False
            for t in b[b["type"]].get("rich_text", []):
                t["plain_text"] = t["text"]["content"]
        target = self.blocks[pid]
        at = next(i for i, b in enumerate(target) if b.get("id") == after) + 1 if after else len(target)
        target[at:at] = stored_blocks
        return stored_blocks

    def children(self, block_id):
        return self.blocks.get(block_id, [])

    def status(self, pid):
        return board.prop_text(self.pages[pid], "Status")

    def result(self, pid):
        return board.prop_text(self.pages[pid], "Result")

    def text(self, pid):
        out = []
        for b in self.blocks[pid]:
            data = b[b["type"]]
            out.append("".join(t.get("plain_text") or t["text"]["content"] for t in data.get("rich_text", [])))
            for c in data.get("children", []):
                out.append("".join(t["text"]["content"] for t in c[c["type"]]["rich_text"]))
        return "\n".join(out)


def para(text, bid=None):
    return {"id": bid or f"p-{text[:12]}", "type": "paragraph", "has_children": False,
            "paragraph": {"rich_text": [{"plain_text": text}]}}


# --- stub Claude ---------------------------------------------------------------------
calls = []
scripted = []


def fake_run_claude(cmd, cwd, env, timeout_s):
    calls.append({"cmd": cmd, "cwd": Path(cwd), "env": env})
    action = scripted.pop(0)
    return action(Path(cwd)), "raw"


def commit_and(status, summary, questions=()):
    def act(cwd):
        n = len(list(cwd.glob("change*.txt")))
        (cwd / f"change{n}.txt").write_text("done\n")
        g("add", ".", cwd=cwd); g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", f"Mission change {n}", cwd=cwd)
        return {"type": "result", "subtype": "success", "is_error": False, "session_id": "sess-1",
                "structured_output": {"status": status, "summary": summary,
                                      "report": "## What I did\n- Added **change** file\n```\ncode\n```",
                                      "questions": list(questions)},
                "permission_denials": [{"tool_name": "Bash"}]}
    return act


def answer(status, summary, questions=()):
    return lambda cwd: {"subtype": "success", "is_error": False, "session_id": "sess-2",
                        "structured_output": {"status": status, "summary": summary, "report": "Answer text", "questions": list(questions)}}


rm.run_claude = fake_run_claude
rm.find_claude = lambda: "claude.exe"

# the project guess's real command (Claude itself replaced by a stub that captures it)
real_classify, seen = rm.classify, []
rm.run_claude = lambda cmd, cwd, env, timeout_s: (seen.append(cmd) or {"structured_output": {"project": "demo-app"}}, "")
STATE.mkdir(parents=True, exist_ok=True)
picked = real_classify("which project?", ["demo-app", "unclear"])
CLASSIFY_OK = (picked == "demo-app" and seen and seen[0][seen[0].index("--model") + 1] == "claude-opus-5-5"
               and seen[0][seen[0].index("--effort") + 1] == "high" and seen[0][seen[0].index("--tools") + 1] == "")
rm.run_claude = fake_run_claude
guesses, guess_calls = [], []


def fake_classify(prompt, options):
    guess_calls.append((prompt, options))
    return guesses.pop(0) if guesses else "unclear"


rm.classify = fake_classify
args = types.SimpleNamespace(max=10, timeout_min=60, dry_run=False)
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def run_board(n, dry=False):
    """Same steps as run_missions.main(), against the fake board."""
    a = types.SimpleNamespace(max=10, timeout_min=60, dry_run=dry)
    if not dry:
        rm.flush_pending(n)
        board.sync_project_options(n, cfg)
        rm.recover_interrupted(n, "db-1")
        rm.clean_done_worktrees(n, "db-1")
    ready = rm.pick_missions(n, "db-1")
    if not dry:
        rm.accept_new_rows(n, cfg, ready)
        rm.safe_refresh(n, cfg)
    order = []
    projects = board.list_projects(cfg)
    for p in ready:
        order.append(p["id"])
        try:
            if rm.run_one(n, cfg, p, projects, a) == "stop":
                break
        except notion_api.NotionError:
            break
        if not dry:
            rm.safe_refresh(n, cfg)
    if not dry:
        rm.safe_refresh(n, cfg)
    return order


# ===== Round 1 ===========================================================================
n = FakeNotion()
n.add("3febc278-9f1d-8100-a000-aaaaaaaa0001", "Add change file", "Ready", "demo-app", "Normal",
      created="2026-10-19T08:00:00Z", body=[para("Please add a change file."), para("עברית בסדר")])
n.add("3febc278-9f1d-8100-a000-bbbbbbbb0002", "Urgent one", "Ready", "demo-app", "High", created="2026-10-19T09:00:00Z")
n.add("3febc278-9f1d-8100-a000-cccccccc0003", "Edited by stranger", "Ready", "demo-app", editor=STRANGER)
n.add("3febc278-9f1d-8100-a000-dddddddd0004", "No project chosen", "Ready", "")
n.add("3febc278-9f1d-8100-a000-eeeeeeee0005", "Research question", "Ready", board.NO_PROJECT, "Low")
n.add("3febc278-9f1d-8100-a000-ffffffff0006", "Draft mission", "Draft", "demo-app")
n.add("3febc278-9f1d-8100-a000-999999990009", "Left running", "Running", "demo-app")
n.add("3febc278-9f1d-8100-a000-121212120012", "Unknown project", "Ready", "no-such-folder")

# the left-over Running mission has already been cut off twice: this third time it's given up
STATE.mkdir(parents=True, exist_ok=True)
(STATE / "attempts.json").write_text(json.dumps({board.short_id("3febc278-9f1d-8100-a000-999999990009"): 2}))

# dry run first: must not write anything
before = json.dumps(n.pages)
run_board(n, dry=True)
check("dry run changes nothing", json.dumps(n.pages) == before)

scripted[:] = [commit_and("done", "Urgent done"), commit_and("done", "Change added"),
               answer("needs_info", "Need a decision", ["Which colour?", "Which page?"])]
order = run_board(n)
check("priority order: High first, then oldest, Low last",
      order[:2] == ["3febc278-9f1d-8100-a000-bbbbbbbb0002", "3febc278-9f1d-8100-a000-aaaaaaaa0001"]
      and order.index("3febc278-9f1d-8100-a000-eeeeeeee0005") > order.index("3febc278-9f1d-8100-a000-aaaaaaaa0001"),
      str(order))
check("left-over Running cut off 3 times -> Failed", n.status("3febc278-9f1d-8100-a000-999999990009") == "Failed"
      and "Gave up after 3" in n.result("3febc278-9f1d-8100-a000-999999990009"))
check("draft untouched", n.status("3febc278-9f1d-8100-a000-ffffffff0006") == "Draft")
check("stranger-edited mission not run", n.status("3febc278-9f1d-8100-a000-cccccccc0003") == "Needs info"
      and "someone other than you" in n.result("3febc278-9f1d-8100-a000-cccccccc0003"))
check("no project -> Needs info", n.status("3febc278-9f1d-8100-a000-dddddddd0004") == "Needs info")
check("unknown project -> Needs info", "no project folder" in n.result("3febc278-9f1d-8100-a000-121212120012"))
check("missions sharing an id prefix get their own folders", len({board.short_id(p) for p in n.pages}) == len(n.pages))
check("only 3 Claude runs", len(calls) == 3, str(len(calls)))

A = "3febc278-9f1d-8100-a000-aaaaaaaa0001"
check("done -> Needs review", n.status(A) == "Needs review", n.status(A))
check("summary on card", n.result(A) == "Change added")
branch = board.prop_text(n.pages[A], "Branch")
check("branch recorded", branch.startswith("mission/") and f"{board.short_id(A)}-add-change-file" in branch, branch)
wt = STATE / "wt" / board.short_id(A)
check("worktree exists on branch", g("rev-parse", "--abbrev-ref", "HEAD", cwd=wt) == branch)
check("main checkout untouched", g("rev-parse", "--abbrev-ref", "HEAD") == "main"
      and (REPO / "wip.txt").exists() and not (REPO / "change0.txt").exists())
check("report appended with commits", "Claude's report" in n.text(A) and "Mission change 0" in n.text(A)
      and "1 commit(s)" in n.text(A), n.text(A))
check("report shows blocked actions + resume hint", "Blocked actions" in n.text(A) and "claude --resume sess-1" in n.text(A))

cmd = calls[1]["cmd"]
prompt = cmd[cmd.index("-p") + 1]
check("prompt carries the mission body (incl. Hebrew)", "Please add a change file." in prompt and "עברית בסדר" in prompt)
check("mission saved to file", (STATE / "attachments" / board.short_id(A) / "mission.md").read_text(encoding="utf-8").count("Please add") == 1)
check("ran in the worktree", calls[1]["cwd"] == wt)
check("auto mode + no prompts + no MCP", all(f in cmd for f in ["auto", "--permission-prompts", "none", "--strict-mcp-config"]))
check("project guess runs Opus 5.5 at high effort, without tools", CLASSIFY_OK)
check("missions run Opus 5.5 at high effort",
      cmd[cmd.index("--model") + 1] == "claude-opus-5-5" and cmd[cmd.index("--effort") + 1] == "high")
check("push deny rules present", "Bash(git push*)" in cmd and "PowerShell(git push*)" in cmd)
check("normal checkout added read-only dir", str(REPO) in cmd[cmd.index("--add-dir"):])
schema = json.loads(cmd[cmd.index("--json-schema") + 1])
check("schema valid JSON", schema["required"] == ["status", "summary", "report", "questions"])
rules = cmd[cmd.index("--append-system-prompt") + 1]
check("rules mention worktree + never push", str(wt) in rules and "Never push" in rules)

env = calls[1]["env"]
check("no Anthropic key / Notion token in child env", not any(k in env for k in ("ANTHROPIC_API_KEY", "NOTION_TOKEN")))
push = subprocess.run(["git", "-C", str(wt), "push", "origin", "HEAD"], capture_output=True, text=True, env=env)
check("git push blocked inside the worktree", push.returncode != 0 and "push-disabled-by-mission-runner" in push.stderr, push.stderr[-200:])

E = "3febc278-9f1d-8100-a000-eeeeeeee0005"
check("no-project mission -> Needs info with questions", n.status(E) == "Needs info"
      and "Which colour?" in n.text(E) and "set Status back to Ready" in n.text(E))
check("no-project ran in scratch folder", calls[2]["cwd"] == STATE / "scratch" / board.short_id(E))

# ===== Round 1b: hands-off missions ===========================================================
n.add("3febc278-9f1d-8100-a000-777777770007", "Added by Claude for me", "Ready", "demo-app", editor=BOT,
      created="2026-10-19T10:00:00Z")
n.add("3febc278-9f1d-8100-a000-888888880008", "New row, no status, settled", "", "demo-app",
      created="2026-10-19T10:01:00Z", edited="2026-10-19T08:00:00.000Z")
n.add("3febc278-9f1d-8100-a000-666666660006", "New row, still being typed", "", "demo-app",
      created="2026-10-19T10:02:00Z", edited=NOW_Z())
calls.clear()
scripted[:] = [answer("done", "G done"), answer("done", "H done")]
run_board(n)
check("mission added by the integration runs", n.status("3febc278-9f1d-8100-a000-777777770007") == "Needs review")
check("settled row with no Status runs", n.status("3febc278-9f1d-8100-a000-888888880008") == "Needs review")
check("row edited in the last 10 min is left alone", n.status("3febc278-9f1d-8100-a000-666666660006") == ""
      and n.result("3febc278-9f1d-8100-a000-666666660006") == "" and len(calls) == 2, str(len(calls)))

# ===== Round 1c: no Project chosen, empty rows ==================================================
G1, BLANK = "3febc278-9f1d-8100-a000-0000000c0071", "3febc278-9f1d-8100-a000-0000000c0072"
n.add(G1, "Replace calendar dots", "", "", created="2026-10-19T10:05:00Z",
      body=[para("in calendar replace the dots for unavailable days")])
n.add(BLANK, "", "", "", created="2026-10-19T10:06:00Z")
guesses[:] = ["demo-app"]
guess_calls.clear()
calls.clear()
scripted[:] = [answer("done", "Dots replaced")]
run_board(n)
check("no Project chosen: Claude picks it, the card shows it, the mission runs",
      board.prop_text(n.pages[G1], "Project") == "demo-app" and n.status(G1) == "Needs review", n.status(G1))
prompt, options = guess_calls[0] if guess_calls else ("", [])
check("the guess sees the mission text and can say 'unclear' or 'no project'",
      "replace the dots" in prompt and "demo-app" in options and "unclear" in options and board.NO_PROJECT in options)
check("an empty row is ignored", n.status(BLANK) == "" and n.result(BLANK) == "" and len(calls) == 1)
D = "3febc278-9f1d-8100-a000-dddddddd0004"
check("unclear project -> Needs info asking to pick one", n.status(D) == "Needs info" and "couldn't tell" in n.result(D), n.result(D))

# ===== Round 2: follow-up on A, usage limit on E ===========================================
n.pages[A]["properties"]["Status"] = stored({"select": {"name": "Ready"}})
n.pages[A]["last_edited_by"] = {"id": OWNER}
n.blocks[A] = n.blocks[A] + [para("Answer: blue")]
n.pages[E]["properties"]["Status"] = stored({"select": {"name": "Ready"}})
n.pages[E]["last_edited_by"] = {"id": OWNER}
calls.clear()
scripted[:] = [lambda cwd: {"is_error": True, "subtype": "error_during_execution", "result": "Claude usage limit reached. Resets 5pm",
                            "session_id": "s"}]
# E is Low, A is Normal -> A runs first; make A hit the limit and E must not run
order = run_board(n)
check("usage limit: stop after first", len(calls) == 1, str(len(calls)))
check("usage limit: mission back to Ready + waiting note", n.status(A) == "Ready" and rm.WAITING in n.result(A), n.result(A))
check("follow-up reused the worktree", calls[0]["cwd"] == wt)
check("follow-up prompt includes earlier report + answer", "Answer: blue" in calls[0]["cmd"][calls[0]["cmd"].index("-p") + 1]
      and "Claude's report" in calls[0]["cmd"][calls[0]["cmd"].index("-p") + 1])

calls.clear()
scripted[:] = [commit_and("done", "Blue applied"), answer("done", "Researched")]
run_board(n)
check("mission handed back after the usage limit runs again", len(calls) == 2 and n.status(A) == "Needs review", n.status(A))
check("follow-up commits counted from main", "2 commit(s)" in n.text(A), n.text(A)[-400:])

# ===== Round 3: Done -> worktree cleaned, branch kept ===========================================
n.pages[A]["properties"]["Status"] = stored({"select": {"name": "Done"}})
run_board(n)
check("done mission's worktree removed", not wt.exists())
check("branch kept", branch in g("branch", "--list", "mission/*"))

# ===== Round 4: cut-off runs and Notion outages ==================================================
OFFLINE = {"is_error": True, "subtype": "success", "api_error_status": None,
           "result": "API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)"}
RUN1, R1, R2 = ("3febc278-9f1d-8100-a000-0000000a0041", "3febc278-9f1d-8100-a000-0000000a0042",
                "3febc278-9f1d-8100-a000-0000000a0043")
n.add(RUN1, "Was running when the PC went off", "Running", "demo-app", created="2026-10-19T11:00:00Z")
calls.clear()
scripted[:] = [commit_and("done", "Finished after resume")]
run_board(n)
check("Running left-over resumes in the same run and finishes", n.status(RUN1) == "Needs review" and len(calls) == 1)
check("attempt counter cleared after finishing", board.short_id(RUN1) not in rm._attempts())

n.add(R1, "Network drops", "Ready", "demo-app", created="2026-10-19T11:10:00Z")
n.add(R2, "Waits behind it", "Ready", "demo-app", created="2026-10-19T11:20:00Z")
calls.clear()
scripted[:] = [lambda cwd: OFFLINE]
run_board(n)
check("lost connection -> back to Ready with a note", n.status(R1) == "Ready"
      and "Paused: the connection to Claude dropped" in n.result(R1), n.result(R1))
check("lost connection stops the run (next mission waits)", len(calls) == 1 and n.status(R2) == "Ready")
check("no report posted for a cut-off run", "Claude's report" not in n.text(R1))
scripted[:] = [lambda cwd: OFFLINE]
run_board(n)
scripted[:] = [lambda cwd: OFFLINE, answer("done", "R2 done")]
run_board(n)
check("third cut-off in a row -> Failed", n.status(R1) == "Failed" and "Gave up after 3 tries" in n.result(R1), n.result(R1))
scripted[:] = [answer("done", "R2 done")]
run_board(n)
check("next mission runs once the stuck one is settled", n.status(R2) == "Needs review")

P1, P2 = "3febc278-9f1d-8100-a000-0000000a0051", "3febc278-9f1d-8100-a000-0000000a0052"
n.add(P1, "Notion down when reporting", "Ready", "demo-app", created="2026-10-19T12:00:00Z")
calls.clear()
def done_but_notion_down(cwd):
    n.fail_append = 1
    return answer("done", "P1 done")(cwd)
scripted[:] = [done_but_notion_down]
run_board(n)
pending = STATE / "pending" / f"{board.short_id(P1)}.json"
check("result kept locally when Notion is unreachable", pending.exists() and n.status(P1) == "Running")
run_board(n)
check("kept result sent on the next run (not marked interrupted)", not pending.exists()
      and n.status(P1) == "Needs review" and n.text(P1).count("Claude's report") == 1, n.status(P1))

n.add(P2, "Status update fails after report", "Ready", "demo-app", created="2026-10-19T12:10:00Z")
def report_ok_status_fails(cwd):
    n.fail_next_update = 1
    return answer("done", "P2 done")(cwd)
scripted[:] = [report_ok_status_fails]
run_board(n)
run_board(n)
check("half-sent result finished without posting the report twice",
      n.status(P2) == "Needs review" and n.text(P2).count("Claude's report") == 1, f"{n.status(P2)} {n.text(P2).count('Claude')}")

# ===== report lists only the mission's own commits ====================================================
g("checkout", "-q", "-b", "someone-else", "main")
(REPO / "other.txt").write_text("pushed by another session\n")
g("add", "other.txt"); g("commit", "-q", "-m", "Another session's pushed work")
g("update-ref", "refs/remotes/origin/main", "HEAD")      # on GitHub's main, not in local main
g("checkout", "-q", "main")
wt_rb = STATE / "wt" / "rebase-case"
g("worktree", "add", "-q", "-b", "mission/rebase-case", str(wt_rb), "origin/main")
(wt_rb / "mine.txt").write_text("mission work\n")
g("add", "mine.txt", cwd=wt_rb); g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "Mission's own commit", cwd=wt_rb)
commits_rb, _ = rm.git_summary(rm.Workspace(wt_rb, "worktree", REPO, "mission/rebase-case", "main", wt_rb))
check("commit list leaves out other sessions' work from origin/main",
      len(commits_rb) == 1 and commits_rb[0].endswith("Mission's own commit"), str(commits_rb))
g("update-ref", "-d", "refs/remotes/origin/main")

# ===== Live view ======================================================================================
import datetime as _dt
V = FakeNotion()
vcfg = dict(cfg)
vcfg.pop("status_block_id", None)
LIVE_RUN, Q1, Q2, QS = ("3febc278-9f1d-8100-a000-0000000b0061", "3febc278-9f1d-8100-a000-0000000b0062",
                        "3febc278-9f1d-8100-a000-0000000b0063", "3febc278-9f1d-8100-a000-0000000b0064")
V.add(LIVE_RUN, "Fix the actor calendar", "Running", "demo-app")
V.pages[LIVE_RUN]["properties"]["Last run"] = stored({"date": {"start": (_dt.datetime.now().astimezone()
                                                                        - _dt.timedelta(minutes=14)).isoformat(timespec="seconds")}})
V.add(Q1, "Second in line", "Ready", "demo-app", created="2026-10-19T09:00:00Z")
V.add(Q2, "First in line (High)", "Ready", "demo-app", priority="High", created="2026-10-19T10:00:00Z")
V.pages[Q1]["properties"]["Result"] = stored({"rich_text": notion_api.rich_text("Paused: the connection to Claude dropped. x")})
V.add(QS, "Edited by a stranger", "Ready", "demo-app", editor=STRANGER, created="2026-10-19T08:00:00Z")
V.add("3febc278-9f1d-8100-a000-0000000b0065", "Finished one", "Needs review", "demo-app")
V.add("3febc278-9f1d-8100-a000-0000000b0066", "Parked", "Draft", "demo-app")

# a transcript like Claude Code writes for the running mission's worktree
tdir = TRANSCRIPTS / f"C--Users-x-wat-framework--tmp-notion-missions-wt-{board.short_id(LIVE_RUN)}"
tdir.mkdir()
events = [
    {"type": "summary"},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "TodoWrite", "input": {"todos": [
        {"content": "Read the calendar", "activeForm": "Reading the calendar", "status": "completed"},
        {"content": "Fix the day editor", "activeForm": "Fixing the day editor", "status": "in_progress"},
        {"content": "Test", "activeForm": "Testing", "status": "pending"},
        {"content": "Commit", "activeForm": "Committing", "status": "pending"}]}}]}},
    {"type": "user", "message": {"content": "tool result"}},
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "Now the tests."},
                                                  {"type": "tool_use", "name": "Bash",
                                                   "input": {"command": "npm test", "description": "Run the calendar tests"}}]}},
]
(tdir / "session.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

live.refresh(V, vcfg)
run_line = V.result(LIVE_RUN)
check("running card shows minutes, step and action",
      run_line == "Working · 14 min · Step 2/4: Fixing the day editor · Run the calendar tests", run_line)
check("waiting cards show their place in line (High first)",
      V.result(Q2) == "Waiting · #1 in line" and V.result(Q1).startswith("Waiting · #2 in line · Paused"), f"{V.result(Q2)} | {V.result(Q1)}")
check("stranger-edited card gets no write (its edit stays visible to the safety check)",
      V.result(QS) == "" and V.pages[QS]["last_edited_by"]["id"] == STRANGER)
bid = vcfg.get("status_block_id")
ids = [b["id"] for b in V.blocks["parent-1"]]
check("live status box created right above the board", bid and ids.index(bid) == ids.index("db-block") - 1, str(ids))
summary = V.block_text(bid)
check("summary says what's running, waiting and finished",
      "🔄 Working on: Fix the actor calendar · 14 min · Step 2/4" in summary and "⏳ Not started: 2 in line · 📝 1 draft" in summary
      and "✅ Finished: 1 to check · 0 done" in summary, summary)
live.refresh(V, vcfg)
check("second refresh updates the same box", len([b for b in V.blocks["parent-1"] if b["type"] == "callout"]) == 1)
V.deleted.add(bid)
live.refresh(V, vcfg)
check("deleted box is recreated", vcfg["status_block_id"] != bid
      and len([b for b in V.blocks["parent-1"] if b["type"] == "callout" and b["id"] not in V.deleted]) == 1)
check("queue text keeps the pause note but not the old place",
      live.queue_text(3, "Waiting · #1 in line · Paused: x") == "Waiting · #3 in line · Paused: x"
      and live.queue_text(2, "Claude is working on this…") == "Waiting · #2 in line")
check("commands without a description never show their arguments",
      live.describe_tool("Bash", {"command": "API_KEY=abc123 node scripts/x.js --token y"}) == "Running node")
V.pages[LIVE_RUN]["properties"]["Status"] = stored({"select": {"name": "Needs review"}})
live.refresh(V, vcfg)
check("idle summary when nothing runs", "💤 Not working on anything right now." in V.block_text(vcfg["status_block_id"]))

# ===== projects that are repo subfolders / untracked folders ======================================
n.add("3febc278-9f1d-8100-a000-131313130013", "Site fix", "Ready", "demo-site")
n.add("3febc278-9f1d-8100-a000-141414140014", "Ignored folder", "Ready", "demo-ignored")
projects = board.list_projects(cfg)
SITE = "3febc278-9f1d-8100-a000-131313130013"
ws_site = rm.prepare_workspace(n.pages["3febc278-9f1d-8100-a000-131313130013"], "demo-site", projects, "Site fix")
check("tracked subfolder -> worktree of the enclosing repo, cwd in the subfolder",
      ws_site.kind == "worktree" and ws_site.root == STATE / "wt" / board.short_id(SITE)
      and ws_site.cwd == STATE / "wt" / board.short_id(SITE) / "site" and (ws_site.cwd / "index.html").exists(),
      f"{ws_site.kind} {ws_site.cwd}")
check("subfolder rules name both folders", str(ws_site.cwd) in ws_site.describe() and str(ws_site.root) in ws_site.describe())
ws_ign = rm.prepare_workspace(n.pages["3febc278-9f1d-8100-a000-141414140014"], "demo-ignored", projects, "Ignored")
check("folder inside a repo but untracked -> not treated as that repo", ws_ign.kind != "worktree", ws_ign.kind)

# ===== timeout + unreadable output ==========================================================
out = rm.parse_outcome({"_timeout": True}, "")
check("timeout -> retry (not stop the run)", out["status"] == "retry" and "time limit" in out["why"] and not out.get("stop_run"))
out = rm.parse_outcome({"is_error": True, "subtype": "success", "api_error_status": None,
                        "result": "API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)"}, "")
check("real ENOTFOUND output -> retry + stop the run", out["status"] == "retry" and out.get("stop_run"))
out = rm.parse_outcome({"is_error": True, "result": "Claude usage limit reached"}, "")
check("usage limit -> limit", out["status"] == "limit")
out = rm.parse_outcome({"is_error": True, "result": "Something unexpected", "api_error_status": 400}, "")
check("other error -> failed", out["status"] == "failed")
out = rm.parse_outcome(None, "garbage")
check("unreadable -> failed", out["status"] == "failed")
out = rm.parse_outcome({"subtype": "success", "is_error": False, "result": json.dumps({"status": "done", "summary": "s", "report": "r", "questions": []})}, "")
check("JSON in result text understood", out["status"] == "done" and out["summary"] == "s")
out = rm.parse_outcome({"subtype": "success", "is_error": False, "result": "Plain text answer\nmore"}, "")
check("plain text result -> done with report", out["status"] == "done" and out["report"].startswith("Plain"))

# ===== markdown + real subprocess plumbing ======================================================
blocks = notion_api.markdown_to_blocks("# Title\n- a **b** `c`\n1. one\n- [x] done\n```\nx = 1\n```\n> q\nplain\n" + "y" * 4500)
types_ = [b["type"] for b in blocks]
check("markdown blocks", types_ == ["heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "code", "quote", "paragraph", "paragraph"], str(types_))
check("long text split under 2000", all(len(t["text"]["content"]) <= 2000 for t in blocks[-1]["paragraph"]["rich_text"]))

fake = HERE / "fake_claude.py"
fake.write_text(
    "import json, sys, os\n"
    "a = sys.argv[1:]\n"
    "json.dump({'argv': a, 'git': os.environ.get('GIT_CONFIG_COUNT')}, open(os.path.join(os.path.dirname(__file__), 'argv.json'), 'w', encoding='utf-8'))\n"
    "print('noise line')\n"
    "print(json.dumps({'subtype': 'success', 'is_error': False, 'structured_output': {'status': 'done', 'summary': 'ok', 'report': 'r', 'questions': []}}))\n",
    encoding="utf-8")
real_run = rm.__dict__["run_claude"]
import importlib
rm2 = importlib.reload(rm)
rm2.STATE_DIR = STATE
ws = rm2.Workspace(WORK, "scratch")
prompt = rm2.build_prompt('Quote "test" & <tags>', "demo-app", "", "line1\nשורה בעברית\n  indented $HOME %PATH%", STATE / "m.md")
cmd = [sys.executable, str(fake)] + rm2.claude_command(prompt, "rules\nwith \"quotes\"", "t", ws, STATE)[1:]
res, raw = rm2.run_claude(cmd, WORK, rm2.child_env(), 30)
got = json.load(open(HERE / "argv.json", encoding="utf-8"))
check("subprocess: prompt arrives intact (quotes, Hebrew, newlines, $ and %)", got["argv"][1] == prompt)
check("subprocess: schema arg intact", json.loads(got["argv"][got["argv"].index("--json-schema") + 1]) == rm2.RESULT_SCHEMA)
check("subprocess: git push block env passed", got["git"] == "6")
check("subprocess: last JSON line parsed past noise", res and res["structured_output"]["summary"] == "ok")

print("\nFAILED: " + ", ".join(fails) if fails else "\nALL PASSED")
