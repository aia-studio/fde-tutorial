"""资源限制。

计划里这一层原本叫 `launcher.py`，实现时改成「父进程侧设限 + 启动期 shim」：
多套一层引导进程会让 `multiprocessing` 的 spawn 子进程重新执行用户代码，
还会让进程树清理多一层，收益不抵成本。

Windows 用 Job Object（带 KILL_ON_JOB_CLOSE，子进程随作业一起死）；
POSIX 用 `RLIMIT_AS`，通过 preexec_fn 在 fork 之后、exec 之前设置。
"""

from __future__ import annotations

import ctypes
import os
import sys

MEM_LIMIT_BYTES = 512 * 1024 * 1024

_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JobObjectExtendedLimitInformation = 9
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_ulong),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_ulong),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_ulong),
        ("SchedulingClass", ctypes.c_ulong),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def memory_limit_supported() -> bool:
    if os.name == "nt":
        return True
    return sys.platform.startswith(("linux", "darwin"))


def apply_windows_job(pid: int, limit_bytes: int = MEM_LIMIT_BYTES):
    """把进程塞进一个带内存上限的 Job Object，返回句柄（失败返回 None）。"""
    if os.name != "nt":
        return None

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None

    info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = (
        _JOB_OBJECT_LIMIT_PROCESS_MEMORY | _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    info.ProcessMemoryLimit = ctypes.c_size_t(limit_bytes)

    ok = kernel32.SetInformationJobObject(
        ctypes.c_void_p(job),
        _JobObjectExtendedLimitInformation,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    if not ok:
        kernel32.CloseHandle(ctypes.c_void_p(job))
        return None

    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(_PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, pid)
    if not handle:
        kernel32.CloseHandle(ctypes.c_void_p(job))
        return None

    assigned = kernel32.AssignProcessToJobObject(ctypes.c_void_p(job), ctypes.c_void_p(handle))
    kernel32.CloseHandle(ctypes.c_void_p(handle))
    if not assigned:
        kernel32.CloseHandle(ctypes.c_void_p(job))
        return None
    return job


def close_windows_job(job) -> None:
    if os.name != "nt" or not job:
        return
    try:
        ctypes.WinDLL("kernel32").CloseHandle(ctypes.c_void_p(job))
    except OSError:
        pass


def posix_preexec(limit_bytes: int = MEM_LIMIT_BYTES):
    """返回给 subprocess 的 preexec_fn；非 POSIX 返回 None。"""

    def _apply() -> None:  # pragma: no cover - 只在 POSIX 子进程里跑
        import resource

        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (ValueError, OSError):
            pass

    if os.name == "nt":
        return None
    return _apply
