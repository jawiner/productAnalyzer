"""One heavy media job at a time on the video PC (USER 2026-11-19: "renders take turns").

Two videos can be built side by side, but a render, an export or a playbook study's prep each needs
gigabytes of memory. On this 16 GB laptop two at once made Windows swap to disk (renders went from
0.8 to 3-7 s a frame) and one render was killed out of memory. So every heavy step takes this turn
first, and the next one waits for it.

As a command (rules.md tells the video runs to use it for renders and exports):

    python C:/Users/97254/wat-framework/tools/content_studio/media_turn.py reelkit render --no-share

It waits for its turn (a line every 5 minutes while it waits), runs the command in the current folder
with the same environment (NODE_OPTIONS included), and exits with the command's exit code. After
MAX_WAIT_S it goes anyway, so a stuck turn can't stop the day's videos.

In Python (the study prep):  with turn("study prep", folder): ...
"""
from __future__ import annotations

import contextlib
import ctypes
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE.parent.parent / ".tmp" / "content_studio"
LOCK = Path(os.environ.get("MEDIA_TURN_LOCK") or STATE / "media.lock")   # the override is for tests
MAX_WAIT_S = 60 * 60    # the other render can take 40-60 min when memory is short; the Bash cap is 120 min
POLL_S = 10
TELL_EVERY_S = 300
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def pid_alive(pid: int) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        try:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                                 creationflags=NO_WINDOW).stdout
        except OSError:
            return False
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def free_gb() -> float:
    """Free physical memory in GB (0 when it can't be read)."""
    class Status(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    try:
        status = Status()
        status.dwLength = ctypes.sizeof(Status)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return status.ullAvailPhys / 1024 ** 3
    except Exception:  # noqa: BLE001 - not Windows, or the call failed
        return 0.0


def holder() -> dict | None:
    """Who has the turn now; None when it's free. A turn whose process has ended is free."""
    try:
        info = json.loads(LOCK.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        # Being written this moment (taken) or left half-written long ago (free).
        try:
            return {"pid": 0, "label": "another job"} if time.time() - LOCK.stat().st_mtime < 30 else None
        except FileNotFoundError:
            return None
    return info if pid_alive(int(info.get("pid") or 0)) else None


def try_take(label: str, project: Path) -> bool:
    STATE.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if holder():
                return False
            with contextlib.suppress(FileNotFoundError):
                LOCK.unlink()
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # free_gb is the memory the job starts with: the worker warns the owner when a render starts low.
            json.dump({"pid": os.getpid(), "label": label, "project": str(project),
                       "since": dt.datetime.now().isoformat(timespec="seconds"), "free_gb": round(free_gb(), 1)}, f)
        return True
    return False


def release() -> None:
    with contextlib.suppress(FileNotFoundError, ValueError, OSError):
        if int(json.loads(LOCK.read_text(encoding="utf-8")).get("pid") or 0) == os.getpid():
            LOCK.unlink()


def wait_turn(label: str, project: Path, say=print, max_wait_s: float = MAX_WAIT_S) -> bool:
    """Blocks until this process has the turn. False = waited max_wait_s and goes without it."""
    start = time.time()
    told = -TELL_EVERY_S
    while not try_take(label, project):
        waited = time.time() - start
        other = holder() or {}
        if waited >= max_wait_s:
            say(f"media_turn: waited {int(waited // 60)} min for {other.get('label', 'another job')}; going anyway")
            return False
        if waited - told >= TELL_EVERY_S:
            say(f"media_turn: waiting for {other.get('label', 'another job')} in {other.get('project', '?')} "
                f"(since {other.get('since', '?')}). This is normal: keep waiting in the foreground.")
            told = waited
        time.sleep(POLL_S)
    return True


@contextlib.contextmanager
def turn(label: str, project: Path, say=print, max_wait_s: float = MAX_WAIT_S):
    got = wait_turn(label, project, say, max_wait_s)
    try:
        yield got
    finally:
        if got:
            release()


def command(argv: list[str]) -> list[str]:
    exe = shutil.which(argv[0]) or argv[0]
    # reelkit is an npm .cmd shim: run batch files through cmd.exe explicitly.
    if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/c", exe, *argv[1:]]
    return [exe, *argv[1:]]


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    label = " ".join(argv[:2])
    say = lambda message: print(message, flush=True)  # noqa: E731
    with turn(label, Path.cwd(), say=say):
        say(f"media_turn: {label} starts ({free_gb():.1f} GB memory free)")
        return subprocess.call(command(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
