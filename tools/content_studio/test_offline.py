"""Offline checks of the worker's memory gates, retries and clean-up. Takes no job and calls no server.

    python tools/content_studio/test_offline.py

The last part starts a fake Claude (a .cmd file) that leaves a Node process running the way a render
started from Git Bash does, and checks the worker stops it, after a normal end and after a timeout.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import worker  # noqa: E402

passed = failed = 0


def check(label: str, ok: bool, got=None) -> None:
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"FAIL  {label}" + (f"  (got {got!r})" if got is not None else ""))


TMP = Path(tempfile.mkdtemp(prefix="content-studio-test-"))
worker.STATE = TMP / "state"
worker.LOG = worker.STATE / "worker.log"
worker.MEMORY_NOTE = worker.STATE / "memory-wait.json"
worker.VIDEO_SLOTS = [worker.STATE / "worker.lock", worker.STATE / "worker-2.lock"]


class FakeEngine:
    def __init__(self, job=None):
        self.calls, self.job = [], job

    def call(self, action, **body):
        self.calls.append((action, body))
        return {"job": self.job} if action == "claim" else {}

    def progress(self, video_id, note):
        self.calls.append(("progress", {"note": note}))


# --- retry_folder: the video's own folder, also after the owner's "Try again" ------------------------------
proj = TMP / "2026-11-22-journal"
proj.mkdir(parents=True)
(proj / "BRIEF.md").write_text("# Video brief\nVideo id: abc-123\n", encoding="utf-8")
job = lambda **v: {"video": {"id": "abc-123", "attempts": 1, "project_dir": str(proj), **v}}  # noqa: E731
check("Try again (attempts back to 1) reuses the video's own folder", worker.retry_folder(job()) == proj)
check("a folder whose brief is another video's isn't reused",
      worker.retry_folder(job(id="other-9")) is None)
check("a later claim reuses the folder as before", worker.retry_folder(job(id="other-9", attempts=2)) == proj)
check("no folder recorded: a new one", worker.retry_folder(job(project_dir=None)) is None)
check("a folder that's gone: a new one", worker.retry_folder(job(project_dir=str(TMP / "gone"))) is None)

# --- last_session: from the result line, or Claude's session files after a timeout -------------------------
sessions = TMP / "sessions"
(proj / "out").mkdir()
(proj / "out" / "claude-run.log").write_text('noise\n{"type":"result","session_id":"11111111-2222-3333-4444-555555555555"}\n',
                                             encoding="utf-8")
check("session from the result line", worker.last_session(proj, sessions) == "11111111-2222-3333-4444-555555555555")
(proj / "out" / "claude-run.log").write_text("", encoding="utf-8")  # a run stopped at the time limit
check("no result and no session files: none", worker.last_session(proj, sessions) is None)
folder = sessions / __import__("re").sub(r"[^A-Za-z0-9]", "-", str(proj))
folder.mkdir(parents=True)
old, new = folder / "aaaaaaaa-0000-0000-0000-000000000000.jsonl", folder / "bbbbbbbb-0000-0000-0000-000000000000.jsonl"
old.write_text("{}"), new.write_text("{}")
os.utime(old, (time.time() - 600, time.time() - 600))
check("timed-out run: the newest session file", worker.last_session(proj, sessions) == new.stem)
check("Claude's folder name for a Windows path",
      __import__("re").sub(r"[^A-Za-z0-9]", "-", r"C:\Users\97254\lifemaxing-independent\marketing\video\daily\2026-11-22-x-2")
      == "C--Users-97254-lifemaxing-independent-marketing-video-daily-2026-11-22-x-2")

# --- wait_for_memory -----------------------------------------------------------------------------------------
class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


eng, clock = FakeEngine(), Clock()
check("enough memory: no wait", worker.wait_for_memory(eng, "v1", "T", sleep=clock.sleep, clock=clock, free=lambda: 5.0) == 0)
check("…and nothing sent", eng.calls == [])

levels = iter([0.7, 1.1, 2.0, 3.4])
eng, clock = FakeEngine(), Clock()
waited = worker.wait_for_memory(eng, "v2", "T", sleep=clock.sleep, clock=clock, free=lambda: next(levels))
check("short at first: waits until there's room", waited == 3 * worker.MEMORY_POLL_S, waited)
check("the owner hears once (low_memory)", [a for a, _ in eng.calls].count("low_memory") == 1, eng.calls)
check("the page shows it's waiting", any(a == "progress" and "Waiting for memory" in b["note"] for a, b in eng.calls))

eng2 = FakeEngine()
levels = iter([0.7, 3.5])
worker.wait_for_memory(eng2, "v2", "T", sleep=clock.sleep, clock=clock, free=lambda: next(levels))
check("the same video isn't announced twice", [a for a, _ in eng2.calls].count("low_memory") == 0, eng2.calls)

eng, clock = FakeEngine(), Clock()
try:
    worker.wait_for_memory(eng, "v3", "T", sleep=clock.sleep, clock=clock, free=lambda: 0.8)
    check("never enough memory: hands the job back", False)
except worker.MemoryShort as e:
    check("never enough memory: hands the job back", True)
    check("…after the wait limit", clock.t - 1000 >= worker.MEMORY_WAIT_S)
    check("…saying what to close", "0.8 GB" in str(e) and "Docker" in str(e), str(e))

# --- run_once: a second video and studies only with room ---------------------------------------------------
calls = []
real = dict(take_video_slot=worker.take_video_slot, video_running=worker.video_running, release=worker.release,
            make_video=worker.make_video, playbook_work=worker.playbook_work, take=worker.take,
            Engine=worker.Engine, free=worker.media_turn.free_gb, sync=worker.playbook.sync_playbook,
            ctx=worker.playbook_ctx)


def scenario(*, slot, busy, gb, job=None):
    calls.clear()
    eng = FakeEngine(job)
    worker.Engine = lambda *_: eng
    worker.take_video_slot = lambda: slot
    worker.video_running = lambda mine=None: busy
    worker.release = lambda lock: None
    worker.take = lambda lock: True
    worker.media_turn.free_gb = lambda: gb
    worker.playbook.sync_playbook = lambda ctx: None
    worker.playbook_ctx = lambda env, engine: None
    worker.make_video = lambda env, engine, job: calls.append("video") or 0
    worker.playbook_work = lambda env, engine: calls.append("study")
    worker.run_once({"CONTENT_ENGINE_URL": "x", "CONTENT_WORKER_SECRET": "y"})
    return calls[:], [a for a, _ in eng.calls]


s1, s2 = worker.VIDEO_SLOTS
got, actions = scenario(slot=s1, busy=False, gb=1.0, job={"video": {}})
check("no other video: claims (the memory wait happens inside the job)", got == ["video"] and "claim" in actions, (got, actions))
got, actions = scenario(slot=s2, busy=True, gb=2.5, job={"video": {}})
check("a video running and 2.5 GB free: no second claim", "claim" not in actions and got == [], (got, actions))
got, actions = scenario(slot=s2, busy=True, gb=9.0, job={"video": {}})
check("a video running and 9 GB free: a second one starts", got == ["video"], (got, actions))
got, actions = scenario(slot=None, busy=True, gb=4.0)
check("both slots busy, memory short: no study", got == [], got)
got, actions = scenario(slot=s1, busy=False, gb=1.5, job=None)
check("nothing to make, 1.5 GB free: no study", got == [], got)
got, actions = scenario(slot=s1, busy=False, gb=6.0, job=None)
check("nothing to make, 6 GB free: a study", got == ["study"], got)
for name, fn in real.items():
    target = {"free": (worker.media_turn, "free_gb"), "sync": (worker.playbook, "sync_playbook"),
              "ctx": (worker, "playbook_ctx")}.get(name, (worker, name))
    setattr(*target, fn)

# --- run_claude: leftovers are stopped, after a normal end and after a timeout --------------------------------
def alive(pid: int) -> bool:
    return str(pid) in subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                                      text=True).stdout


bash = Path(r"C:\Program Files\Git\bin\bash.exe")
node = shutil.which("node")
if os.name == "nt" and bash.exists() and node:
    sleeper = TMP / "sleeper.js"
    sleeper.write_text("require('fs').writeFileSync(process.argv[2], String(process.pid)); setTimeout(() => {}, 120000);")
    for mode in ("finished", "timeout"):
        run_dir = TMP / f"run-{mode}"
        (run_dir / "out").mkdir(parents=True)
        pid_file = TMP / f"leftover-{mode}.pid"
        fake = TMP / f"fake-claude-{mode}.cmd"
        tail = ("echo {\"session_id\":\"s-1\",\"structured_output\":{\"status\":\"done\"}}" if mode == "finished"
                else "ping -n 30 127.0.0.1 >nul")
        # Like a render started from Claude's Git Bash: bash starts node in the background and returns.
        fake.write_text("@echo off\r\n"
                        f"\"{bash}\" -c \"'{Path(node).as_posix()}' '{sleeper.as_posix()}' '{pid_file.as_posix()}' & sleep 2\"\r\n"
                        f"{tail}\r\n", encoding="utf-8")
        t0 = time.time()
        result, _raw = worker.run_claude(run_dir, {"CLAUDE_BIN": str(fake)}, FakeEngine(), "vid",
                                         timeout_s=8 if mode == "timeout" else 90)
        took = time.time() - t0
        pid = int(pid_file.read_text()) if pid_file.exists() else 0
        if mode == "finished":
            check("finished run answered, though a leftover held its output open",
                  (result or {}).get("session_id") == "s-1", result)
            check("…without waiting out the time limit", took < 60, round(took))
        else:
            check("fake run timed out", (result or {}).get("_timeout") is True, result)
            check("…and stopped on time, not when the leftover ended", took < 40, round(took))
        check(f"{mode}: the leftover render-like process started", pid > 0)
        time.sleep(1)
        check(f"{mode}: …and the worker stopped it", pid and not alive(pid), pid)
        if pid and alive(pid):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
else:
    print("skipped the clean-up run checks (needs Windows, Git Bash and node)")

shutil.rmtree(TMP, ignore_errors=True)
print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
