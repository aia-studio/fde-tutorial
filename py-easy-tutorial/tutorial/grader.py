"""判题：把「用户代码 + 隐藏测试」拼成一个脚本，在沙箱里跑，逐条收集结果。

为什么不分进程逐条跑：一门课的测试通常 2–5 条，逐条起进程会让提交延迟变成
好几秒。代价是测试之间共享全局状态，所以约定 —— **测试只做断言，不改状态**。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

from tutorial.limits import apply_windows_job, close_windows_job, posix_preexec
from tutorial.runner import MEM_LIMIT_BYTES, child_env, kill_tree

SENTINEL = "__PYTUT_RESULT__"
DEFAULT_TIMEOUT = 10.0

_HARNESS = """

# ---------------- 判题 外壳 ----------------
import json as _pytut_json

_specs = _pytut_json.loads({specs!r})
_results = []
for _spec in _specs:
    try:
        exec(compile(_spec["code"], "<test>", "exec"), globals())
        _results.append({{"name": _spec["name"], "passed": True, "error": ""}})
    except Exception as _exc:
        _results.append(
            {{
                "name": _spec["name"],
                "passed": False,
                "error": type(_exc).__name__ + ": " + str(_exc),
            }}
        )
print("{sentinel}" + _pytut_json.dumps(_results, ensure_ascii=False))
"""


def build_source(code: str, tests: list[dict]) -> str:
    specs = [{"name": t["name"], "code": t["code"]} for t in tests]
    return code.rstrip() + "\n" + _HARNESS.format(
        specs=json.dumps(specs, ensure_ascii=False), sentinel=SENTINEL
    )


def _parse(stdout: str) -> list[dict] | None:
    marker = stdout.rfind(SENTINEL)
    if marker == -1:
        return None
    payload = stdout[marker + len(SENTINEL) :].strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def grade(
    code: str,
    tests: list[dict],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    mem_limit_mb: int | None = None,
) -> dict:
    """返回 {results, passed, timed_out, stderr, missing_harness}。"""
    if not tests:
        return {
            "results": [],
            "passed": False,
            "timed_out": False,
            "stderr": "这道题没有配置测试",
            "missing_harness": False,
        }

    workdir = tempfile.mkdtemp(prefix="pytut-check-")
    script = os.path.join(workdir, "main.py")
    try:
        with open(script, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_source(code, tests))

        kwargs: dict[str, object] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "cwd": workdir,
            "env": child_env(allow_network=False),
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
            preexec = posix_preexec(mem_limit_mb * 1024 * 1024 if mem_limit_mb else MEM_LIMIT_BYTES)
            if preexec:
                kwargs["preexec_fn"] = preexec

        proc = subprocess.Popen(
            [sys.executable, "-s", "-B", "-u", "main.py"],
            **kwargs,  # type: ignore[arg-type]
        )
        job = None
        if os.name == "nt" and mem_limit_mb:
            job = apply_windows_job(proc.pid, mem_limit_mb * 1024 * 1024)

        timed_out = False
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc.pid)
            try:
                out, err = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                out, err = b"", b""
        finally:
            close_windows_job(job)

        stdout = (out or b"").decode("utf-8", "replace")
        stderr = (err or b"").decode("utf-8", "replace")
        results = _parse(stdout)

        if results is None:
            return {
                "results": [],
                "passed": False,
                "timed_out": timed_out,
                "stderr": stderr.strip(),
                "missing_harness": True,
            }

        return {
            "results": results,
            "passed": bool(results) and all(r["passed"] for r in results),
            "timed_out": timed_out,
            "stderr": stderr.strip(),
            "missing_harness": False,
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def grade_async(code: str, tests: list[dict], *, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """同步接口的别名，方便未来换成线程池而不改调用方。"""
    return grade(code, tests, timeout=timeout)
