"""单步追踪：在子进程里用 sys.settrace 采集每一行的状态。

输出的是**步骤序列**，每一步带：行号、函数名、调用栈、局部变量快照。
可变对象带 `oid`（id() 的值）——两个变量指向同一个列表时 oid 相同，
前端据此画出"同一个对象被多个名字引用"，这正是可变对象教学的关键。

限制（教学场景裁剪，不是通用调试器）：
- 步数 ≤ 3000、栈深 ≤ 40、嵌套展开 ≤ 2 层、字符串截断 60 字符；
- 只跟踪用户代码（按编译文件名过滤），不追踪 import 进来的库；
- 不追踪 asyncio 与线程——事件循环的调度无法用单栈表达，那些课改用时间线图示。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tutorial.limits import apply_windows_job, close_windows_job, posix_preexec
from tutorial.runner import child_env, kill_tree

MAX_STEPS = 3000
MAX_DEPTH = 40
MAX_ITEMS = 20
MAX_STR = 60

SANDBOX = Path(__file__).resolve().parent / "sandbox"
TRACE_MAIN = SANDBOX / "trace_main.py"
DEFAULT_TIMEOUT = 10.0


def _snap(value, depth: int = 0, seen: frozenset = frozenset()) -> dict:
    """把一个值压成紧凑 JSON。oid 只给可能可变/需要比较身份的对象。"""
    if value is None:
        return {"t": "NoneType", "v": "None"}
    if isinstance(value, bool):
        return {"t": "bool", "v": str(value)}
    if isinstance(value, int):
        return {"t": "int", "v": str(value)}
    if isinstance(value, float):
        return {"t": "float", "v": repr(value)}
    if isinstance(value, str):
        text = value if len(value) <= MAX_STR else value[: MAX_STR - 3] + "..."
        return {"t": "str", "v": text, "q": True}

    t = type(value).__name__

    if isinstance(value, bytes):
        return {"t": t, "v": repr(value)[:MAX_STR]}

    if isinstance(value, (list, tuple, set, frozenset, dict)):
        if id(value) in seen or depth >= 2:
            return {"t": t, "v": "…", "oid": id(value)}
        seen2 = seen | {id(value)}
        if isinstance(value, dict):
            items = [
                [_snap(k, depth + 1, seen2), _snap(v, depth + 1, seen2)]
                for k, v in list(value.items())[:MAX_ITEMS]
            ]
            more = len(value) - len(items)
            if more > 0:
                items.append([{"t": "…", "v": f"还有 {more} 项"}])
            return {"t": "dict", "oid": id(value), "items": items}
        if isinstance(value, (set, frozenset)):
            members = sorted(repr(x) for x in list(value)[:MAX_ITEMS])
            return {"t": t, "v": "{" + ", ".join(members) + "}", "oid": id(value)}
        items = [_snap(x, depth + 1, seen2) for x in list(value)[:MAX_ITEMS]]
        return {"t": t, "oid": id(value), "items": items}

    if callable(value):
        name = getattr(value, "__qualname__", t)
        return {"t": "callable", "v": str(name)}

    # 自定义类实例：展开公有属性一层
    if hasattr(value, "__dict__"):
        if id(value) in seen or depth >= 2:
            return {"t": t, "v": f"<{t}>", "oid": id(value)}
        seen2 = seen | {id(value)}
        attrs = {
            k: _snap(v, depth + 1, seen2)
            for k, v in vars(value).items()
            if not k.startswith("_")
        }
        return {"t": t, "oid": id(value), "attrs": attrs, "v": f"<{t}>"}

    return {"t": t, "v": repr(value)[:MAX_STR], "oid": id(value)}


def trace(code: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """在子进程里逐步执行 `code`，返回步骤序列与输出。"""
    workdir = tempfile.mkdtemp(prefix="pytut-trace-")
    main_path = os.path.join(workdir, "main.py")
    out_path = os.path.join(workdir, "trace.json")
    try:
        with open(main_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(code if code.endswith("\n") else code + "\n")

        env = child_env(allow_network=False)
        env["PYTUT_TRACE_ENTRY"] = "1"
        kwargs: dict[str, object] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "cwd": workdir,
            "env": env,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
            preexec = posix_preexec()
            if preexec:
                kwargs["preexec_fn"] = preexec

        proc = subprocess.Popen(
            [sys.executable, "-s", "-B", "-u", TRACE_MAIN, main_path, out_path],
            **kwargs,  # type: ignore[arg-type]
        )
        job = None
        if os.name == "nt":
            job = apply_windows_job(proc.pid)

        timed_out = False
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc.pid)
            try:
                out, err = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                out, err = "", ""
        finally:
            close_windows_job(job)

        payload: dict = {"steps": [], "error": None, "exit_code": proc.returncode}
        try:
            raw = Path(out_path).read_text(encoding="utf-8")
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                payload = loaded
        except (OSError, json.JSONDecodeError):
            # 没有产出 trace：多半是语法错误，用 stderr 说明
            payload = {
                "steps": [],
                "error": (err or "").strip()[-800:],
                "exit_code": proc.returncode,
            }

        if timed_out:
            payload["error"] = "追踪超时（超过 10 秒）。step 块里的代码不要写死循环或等待输入。"
            payload["steps"] = payload.get("steps", [])
        payload["stdout"] = (out or "")[-4000:]
        payload["stderr"] = (err or "")[-4000:]
        payload["timed_out"] = timed_out
        payload["steps"] = payload.get("steps", [])[:MAX_STEPS]
        payload["truncated"] = len(payload["steps"]) >= MAX_STEPS
        return payload
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
