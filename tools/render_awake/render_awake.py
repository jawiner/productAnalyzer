"""Keep the PC awake while a long render runs (USER 2026-11-25: "use Awake during long renders automatically").

Runs in the background from sign-in (task WAT-RenderAwake, see setup_task.ps1). Every 20 s it looks for render work:
  - a node process running `reelkit render|export`, `remotion render` or `hyperframes render`
  - an ffmpeg process that has run for 30 s or more
  - a content studio video, playbook study or render turn (lock files in .tmp/content_studio) held 60 s or more
While there is some, it turns on PowerToys Awake with a 14-minute timer and renews it every 5 minutes. The tray
icon shows it, and if this script dies, Awake turns itself off within 14 minutes. 3 minutes after the last render
ends it sets Awake back to normal.

It never overrides the owner: an Awake session started from the tray (any length except exactly 14 minutes) is
left alone, and if Awake is switched off during a render it stays off until that render is done. If PowerToys
isn't running, this script holds the PC awake itself (the same Windows request Awake makes) and lets go the same
way. On battery at 15% or less it lets go so Windows can sleep. Closing the lid on battery still sleeps.

    python tools/render_awake/render_awake.py            # the loop (the task runs it with pythonw)
    python tools/render_awake/render_awake.py --status   # what it sees now; changes nothing

Log: .tmp/render_awake/render_awake.log (one line per change).
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / ".tmp" / "content_studio"
STATE_DIR = ROOT / ".tmp" / "render_awake"
LOG = STATE_DIR / "render_awake.log"
STATUS = STATE_DIR / "status.json"
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
AWAKE_SETTINGS = LOCALAPPDATA / "Microsoft" / "PowerToys" / "Awake" / "settings.json"
DSC_CANDIDATES = [LOCALAPPDATA / "PowerToys" / "PowerToys.DSC.exe",
                  Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PowerToys" / "PowerToys.DSC.exe"]
MUTEX_NAME = "Local\\WAT-RenderAwake"

POLL_S = 20
GRACE_S = 180            # exports and checks follow a render a minute or two later: don't flicker off between
RENEW_S = 300
OUR_MINUTES = 14         # the mark of a session this script started: the tray offers 30 min, 1 h, 2 h
FFMPEG_MIN_AGE_S = 30
LOCK_MIN_AGE_S = 60      # every 2-min worker pass takes a slot for a moment to look for work
LOCK_MAX_AGE_S = 4 * 3600   # a video run is capped at ~3 h; older = a stale file whose pid was reused
LOW_BATTERY_PCT = 15

RENDER_RE = re.compile(r"(reelkit|remotion|hyperframes)[^\s]*\s+(render|export)\b")
LOCKS = {"worker.lock": "content studio video", "worker-2.lock": "content studio video 2",
         "playbook.lock": "playbook study", "media.lock": "render turn"}

NO_WINDOW = 0x08000000
ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001


# ---------------------------------------------------------------- the decision (no Windows calls; tested offline)

@dataclass
class AwakeState:
    mode: int        # 0 normal, 1 indefinite, 2 timed, 3 until a time
    hours: int
    minutes: int


class Keeper:
    """Decides, each pass, whether to hold the PC awake and how. `io` does the actual calls."""

    def __init__(self, io, *, grace_s: float = GRACE_S, renew_s: float = RENEW_S, minutes: int = OUR_MINUTES):
        self.io, self.grace_s, self.renew_s, self.minutes = io, grace_s, renew_s, minutes
        self.owner = "none"          # "awake" (our Awake timer) | "self" (our own Windows request) | "none"
        self.last_write = 0.0
        self.last_busy: float | None = None
        self.yielded = False         # Awake was switched off during this render: leave it off

    def ours(self, s: AwakeState | None) -> bool:
        return s is not None and s.mode == 2 and s.hours == 0 and s.minutes == self.minutes

    def tick(self, now: float, busy: list[str], low_battery: bool = False) -> str:
        if busy:
            self.last_busy = now
        want = bool(busy) or (self.last_busy is not None and now - self.last_busy < self.grace_s)
        if not want:
            self.last_busy, self.yielded = None, False
            self.release()
            return "idle"
        if low_battery:
            self.release()
            return f"letting go: battery at {LOW_BATTERY_PCT}% or less"
        if self.yielded:
            return "off: Awake was switched off during this render"
        if not self.io.awake_running():
            return self._hold_self()
        if self.owner == "self":
            self.io.hold_self(False)
            self.owner = "none"
        s = self.io.read_awake()
        if s is None:
            return self._hold_self()
        if self.ours(s):
            self.owner = "awake"
            if now - self.last_write >= self.renew_s:
                return self._write_ours(now)
            return "awake"
        if s.mode == 0:
            # Our timer is renewed every few minutes, so seeing it off this soon means someone switched it off.
            # Off after the timer's full length means it ran out while this script was asleep: start again.
            if self.owner == "awake" and now - self.last_write < self.minutes * 60 - 60:
                self.owner, self.yielded = "none", True
                return "off: Awake was switched off during this render"
            return self._write_ours(now)
        self.owner = "none"
        return "your own Awake session is on: leaving it"

    def _write_ours(self, now: float) -> str:
        if self.io.write_awake(2, self.minutes):
            self.owner, self.last_write = "awake", now
            return "awake"
        return self._hold_self()

    def _hold_self(self) -> str:
        if self.owner != "self":
            self.io.hold_self(True)
            self.owner = "self"
        return "holding the PC awake itself (PowerToys Awake not available)"

    def release(self) -> None:
        if self.owner == "self":
            self.io.hold_self(False)
        if self.ours(self.io.read_awake()):
            self.io.write_awake(0, 0)
        self.owner = "none"


# ---------------------------------------------------------------- Windows

if os.name == "nt":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")
    kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    kernel32.OpenProcess.restype = wt.HANDLE
    kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    kernel32.CloseHandle.argtypes = [wt.HANDLE]
    kernel32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
    kernel32.GetProcessTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
    kernel32.GetSystemTimeAsFileTime.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
    kernel32.SetThreadExecutionState.restype = wt.DWORD
    kernel32.SetThreadExecutionState.argtypes = [wt.DWORD]
    kernel32.CreateMutexW.restype = wt.HANDLE
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wt.BOOL, wt.LPCWSTR]
    kernel32.OpenMutexW.restype = wt.HANDLE
    kernel32.OpenMutexW.argtypes = [wt.DWORD, wt.BOOL, wt.LPCWSTR]
    ntdll.NtQueryInformationProcess.restype = ctypes.c_long
    ntdll.NtQueryInformationProcess.argtypes = [wt.HANDLE, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
                                                ctypes.POINTER(ctypes.c_ulong)]

INVALID_HANDLE = ctypes.c_void_p(-1).value
QUERY_LIMITED = 0x1000


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


class UNICODE_STRING(ctypes.Structure):
    _fields_ = [("Length", wt.USHORT), ("MaximumLength", wt.USHORT), ("Buffer", ctypes.c_void_p)]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", wt.BYTE), ("BatteryFlag", wt.BYTE), ("BatteryLifePercent", wt.BYTE),
                ("SystemStatusFlag", wt.BYTE), ("BatteryLifeTime", wt.DWORD), ("BatteryFullLifeTime", wt.DWORD)]


if os.name == "nt":
    for _fn in (kernel32.Process32FirstW, kernel32.Process32NextW):
        _fn.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.GetSystemPowerStatus.argtypes = [ctypes.POINTER(SYSTEM_POWER_STATUS)]


def processes() -> list[tuple[int, str]]:
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap or snap == INVALID_HANDLE:
        return []
    out = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            out.append((entry.th32ProcessID, entry.szExeFile.lower()))
            ok = kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snap)
    return out


def _with_process(pid: int, fn, default):
    h = kernel32.OpenProcess(QUERY_LIMITED, False, pid)
    if not h:
        return default
    try:
        return fn(h)
    except OSError:
        return default
    finally:
        kernel32.CloseHandle(h)


def command_line(pid: int) -> str:
    def read(h):
        size = 4096
        for _ in range(3):
            buf = ctypes.create_string_buffer(size)
            need = ctypes.c_ulong(0)
            status = ntdll.NtQueryInformationProcess(h, 60, buf, size, ctypes.byref(need))  # ProcessCommandLine
            if status == 0:
                us = UNICODE_STRING.from_buffer(buf)
                return ctypes.wstring_at(us.Buffer, us.Length // 2) if us.Buffer else ""
            size = max(need.value, size * 2)
        return ""
    return _with_process(pid, read, "")


def age_s(pid: int) -> float:
    def read(h):
        created, a, b, c = (ctypes.c_ulonglong() for _ in range(4))
        if not kernel32.GetProcessTimes(h, ctypes.byref(created), ctypes.byref(a), ctypes.byref(b), ctypes.byref(c)):
            return 0.0
        now = ctypes.c_ulonglong()
        kernel32.GetSystemTimeAsFileTime(ctypes.byref(now))
        return (now.value - created.value) / 1e7
    return _with_process(pid, read, 0.0)


def alive(pid: int) -> bool:
    def read(h):
        code = wt.DWORD()
        return bool(kernel32.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
    return bool(pid) and _with_process(pid, read, False)


def low_battery() -> bool:
    status = SYSTEM_POWER_STATUS()
    if not kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        return False
    return status.ACLineStatus == 0 and status.BatteryLifePercent != 255 and status.BatteryLifePercent <= LOW_BATTERY_PCT


def lock_jobs(now: float) -> list[str]:
    jobs = []
    for name, label in LOCKS.items():
        path = STUDIO / name
        try:
            age = now - path.stat().st_mtime
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if not LOCK_MIN_AGE_S <= age <= LOCK_MAX_AGE_S:
            continue
        try:
            pid = int(json.loads(text).get("pid") or 0) if text.startswith("{") else int(text or 0)
        except (ValueError, AttributeError):
            continue
        if alive(pid):
            jobs.append(f"{label} (pid {pid})")
    return jobs


def scan(now: float) -> tuple[list[str], bool]:
    """(the render work running now, whether PowerToys Awake is running)."""
    busy, awake_up = [], False
    for pid, exe in processes():
        if exe == "powertoys.awake.exe":
            awake_up = True
        elif exe == "node.exe":
            m = RENDER_RE.search(command_line(pid).replace('"', " ").lower())
            if m:
                busy.append(f"{m.group(1)} {m.group(2)} (pid {pid})")
        elif exe == "ffmpeg.exe" and age_s(pid) >= FFMPEG_MIN_AGE_S:
            busy.append(f"ffmpeg (pid {pid})")
    return busy + lock_jobs(now), awake_up


class WinIO:
    def __init__(self):
        self.awake_up = False
        self.dsc = next((p for p in DSC_CANDIDATES if p.exists()), None)

    def awake_running(self) -> bool:
        return self.awake_up and self.dsc is not None

    def read_awake(self) -> AwakeState | None:
        try:
            p = json.loads(AWAKE_SETTINGS.read_text(encoding="utf-8")).get("properties", {})
            return AwakeState(int(p.get("mode", 0)), int(p.get("intervalHours", 0)), int(p.get("intervalMinutes", 0)))
        except (OSError, ValueError, TypeError, AttributeError):
            return None

    def write_awake(self, mode: int, minutes: int) -> bool:
        if self.dsc is None:
            return False
        props = {"mode": mode} if mode == 0 else {"mode": mode, "intervalHours": 0, "intervalMinutes": minutes,
                                                  "keepDisplayOn": False}
        payload = json.dumps({"settings": {"properties": props, "name": "Awake"}})
        try:
            subprocess.run([str(self.dsc), "set", "--resource", "settings", "--module", "Awake", "--input", payload],
                           capture_output=True, timeout=60, creationflags=NO_WINDOW, check=True)
        except (OSError, subprocess.SubprocessError) as e:
            log(f"couldn't change Awake ({type(e).__name__}): {str(e)[:200]}")
            return False
        s = self.read_awake()
        return s is not None and s.mode == mode

    def hold_self(self, on: bool) -> None:
        kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


# ---------------------------------------------------------------- loop

def log(line: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if LOG.exists() and LOG.stat().st_size > 512 * 1024:
            LOG.replace(LOG.with_suffix(".log.1"))
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')}  {line}\n")
    except OSError:
        pass


def write_status(state: str, busy: list[str], owner: str) -> None:
    try:
        STATUS.write_text(json.dumps({"checked": dt.datetime.now().isoformat(timespec="seconds"), "state": state,
                                      "owner": owner, "renders": busy, "pid": os.getpid()}, indent=1),
                          encoding="utf-8")
    except OSError:
        pass


def show_status() -> int:
    io = WinIO()
    busy, io.awake_up = scan(time.time())
    running = kernel32.OpenMutexW(0x00100000, False, MUTEX_NAME)
    if running:
        kernel32.CloseHandle(running)
    s = io.read_awake()
    print(f"watcher running: {'yes' if running else 'no'}")
    print(f"renders now: {', '.join(busy) or 'none'}")
    print(f"PowerToys Awake running: {'yes' if io.awake_up else 'no'}"
          + (f", mode {s.mode} ({s.hours} h {s.minutes} min)" if s else ""))
    print(f"battery low: {'yes' if low_battery() else 'no'}")
    try:
        print("last status: " + STATUS.read_text(encoding="utf-8").replace("\n", " "))
    except OSError:
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--status", action="store_true", help="show what it sees now and exit; changes nothing")
    ap.add_argument("--poll", type=float, default=POLL_S)
    ap.add_argument("--grace", type=float, default=GRACE_S)
    ap.add_argument("--renew", type=float, default=RENEW_S)
    ap.add_argument("--run-for", type=float, default=0, help="stop after this many seconds (tests)")
    args = ap.parse_args()
    if os.name != "nt":
        print("Windows only", file=sys.stderr)
        return 1
    if args.status:
        return show_status()

    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == 183:      # ERROR_ALREADY_EXISTS
        print("render_awake is already running")
        return 0
    io = WinIO()
    keeper = Keeper(io, grace_s=args.grace, renew_s=args.renew)
    log(f"started (pid {os.getpid()}, every {args.poll:g} s)")
    started, last_key, last_status = time.time(), None, 0.0
    try:
        while not args.run_for or time.time() - started < args.run_for:
            now = time.time()
            busy, io.awake_up = scan(now)
            state = keeper.tick(now, busy, low_battery())
            key = (state, tuple(sorted(busy)))
            changed = key != last_key
            if changed:
                what = ", ".join(busy) or ("render ended, back to normal in a few minutes" if state == "awake"
                                           else "no renders")
                log(f"{state}: {what}")
                last_key = key
            if changed or now - last_status >= 300:
                write_status(state, busy, keeper.owner)
                last_status = now
            time.sleep(args.poll)
    except KeyboardInterrupt:
        pass
    finally:
        keeper.release()
        write_status("stopped", [], "none")
        log("stopped")
        kernel32.CloseHandle(mutex)
    return 0


if __name__ == "__main__":
    sys.exit(main())
