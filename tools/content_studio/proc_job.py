"""Keep everything a video run starts in one Windows job, so it can all be stopped together.

Why (2026-11-22): a run that hit its time limit was stopped with `taskkill /T` on claude.exe, but the
programs it had started from Git Bash (voice trimming with faster-whisper, renders) aren't in claude.exe's
process tree as Windows sees it, so they kept running and holding memory. The retry then started on a PC
with even less memory free, crawled, and timed out too. A process started inside a job stays in that job
whatever starts it, so stopping the job stops all of it.

    job = Job()                  # one per run
    job.add(proc)                # right after subprocess.Popen
    ...
    job.kill()                   # at the end of the run, finished or not
    job.close()

Not Windows, or the job can't be made: every call quietly does nothing, and the old kill still runs.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9
JobObjectBasicProcessIdList = 3
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001


class _IoCounters(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _BasicLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _BasicLimits), ("IoInfo", _IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class Job:
    def __init__(self) -> None:
        self.handle = None
        if os.name != "nt":
            return
        try:
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.CreateJobObjectW.restype = wintypes.HANDLE
            k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            k32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                      wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
            k32.CloseHandle.argtypes = [wintypes.HANDLE]
            self.k32 = k32
            handle = k32.CreateJobObjectW(None, None)
            if not handle:
                return
            info = _ExtendedLimits()
            # Closing the last handle (the worker ending for any reason) also stops the run's processes.
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not k32.SetInformationJobObject(handle, JobObjectExtendedLimitInformation,
                                               ctypes.byref(info), ctypes.sizeof(info)):
                k32.CloseHandle(handle)
                return
            self.handle = handle
        except (OSError, AttributeError):
            self.handle = None

    def add(self, proc) -> bool:
        """Puts a just-started subprocess.Popen in the job. Its children (and theirs) join it as they start."""
        if not self.handle:
            return False
        handle = getattr(proc, "_handle", None)
        return bool(handle) and bool(self.k32.AssignProcessToJobObject(self.handle, int(handle)))

    def pids(self) -> list[int]:
        """The processes still in the job."""
        if not self.handle:
            return []

        class _List(ctypes.Structure):
            _fields_ = [("Assigned", wintypes.DWORD), ("InList", wintypes.DWORD),
                        ("Ids", ctypes.c_size_t * 1024)]
        lst = _List()
        ok = self.k32.QueryInformationJobObject(self.handle, JobObjectBasicProcessIdList, ctypes.byref(lst),
                                                ctypes.sizeof(lst), None)
        return [int(lst.Ids[i]) for i in range(lst.InList)] if ok else []

    def kill(self) -> int:
        """Stops every process in the job; answers how many there were."""
        if not self.handle:
            return 0
        count = len(self.pids())
        self.k32.TerminateJobObject(self.handle, 1)
        return count

    def close(self) -> None:
        if self.handle:
            self.k32.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self) -> "Job":
        return self

    def __exit__(self, *exc) -> None:
        self.kill()
        self.close()
