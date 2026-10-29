"""代码执行：真实 CPython 子进程 + 流式输出 + 超时 + 进程树清理 + 资源限制。

五条硬约束：

1. 用户代码必须在**独立进程**里跑，主进程绝不能因为 `while True` 卡死；
2. 必须能杀掉**整棵进程树**（`multiprocessing` 会派生子进程，只 kill 父进程会留孤儿）；
3. 输出必须有上限，否则 `print` 死循环会把内存吃光；
4. 内存要有上限（Windows：Job Object；POSIX：RLIMIT_AS）；
5. 标准输入要**可交互**——`input()` 是入门课绕不开的东西，不能只做只读演示。
"""

from __future__ import annotations

import codecs
import os
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

from tutorial.limits import (
    MEM_LIMIT_BYTES,
    apply_windows_job,
    close_windows_job,
    posix_preexec,
)

MAX_STDOUT = 256 * 1024
MAX_STDERR = 64 * 1024
DEFAULT_TIMEOUT = 5.0
MAX_TIMEOUT = 15.0
MAX_CONCURRENT = 3

SHIM_DIR = Path(__file__).resolve().parent / "sandbox"

_ENV_KEEP = {
    "PATH",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "LANG",
    "LC_ALL",
}


def _child_env(allow_network: bool) -> dict[str, str]:
    """白名单环境变量：不把用户的 PYTHONPATH / 虚拟环境变量带进沙箱。"""
    env = {k: v for k, v in os.environ.items() if k.upper() in _ENV_KEEP}
    env.update(
        {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(SHIM_DIR),
            "PYTUT_ALLOW_NETWORK": "1" if allow_network else "0",
        }
    )
    return env


def _kill_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=15,
        )
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


class RunJob:
    """一次执行。事件通过 `events` 队列交给 SSE，避免线程直接写 socket。"""

    def __init__(
        self,
        code: str,
        timeout: float,
        *,
        allow_network: bool = False,
        mem_limit_mb: int | None = None,
    ) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.code = code
        self.timeout = timeout
        self.allow_network = allow_network
        self.mem_limit_mb = mem_limit_mb
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.proc: subprocess.Popen[bytes] | None = None
        self.workdir: str | None = None
        self.exit_code: int | None = None
        self.timed_out = False
        self.truncated = False
        self.stdin_closed = False
        self.started_at = 0.0
        self._bytes = {"stdout": 0, "stderr": 0}
        self._limit = {"stdout": MAX_STDOUT, "stderr": MAX_STDERR}
        self._readers: list[threading.Thread] = []
        self._timer: threading.Timer | None = None
        self._finished = threading.Event()
        self._job = None
        self._stdin_lock = threading.Lock()
        self._hard_deadline = 0.0

    # ---- 生命周期 ----

    def start(self) -> None:
        self.workdir = tempfile.mkdtemp(prefix="pytut-run-")
        script = os.path.join(self.workdir, "main.py")
        with open(script, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.code if self.code.endswith("\n") else self.code + "\n")

        kwargs: dict[str, object] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "bufsize": 0,
            "cwd": self.workdir,
            "env": _child_env(self.allow_network),
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
            preexec = posix_preexec(self._mem_bytes())
            if preexec:
                kwargs["preexec_fn"] = preexec

        self.started_at = time.time()
        # 用相对文件名启动，traceback 里就是 `File "main.py", line N`，
        # 前端可以直接把 N 映射回编辑器，不用做路径替换。
        self.proc = subprocess.Popen(
            [sys.executable, "-s", "-B", "-u", "main.py"], **kwargs
        )

        if os.name == "nt" and self.mem_limit_mb:
            self._job = apply_windows_job(self.proc.pid, self._mem_bytes())

        stdout = self.proc.stdout
        stderr = self.proc.stderr
        for stream, name in ((stdout, "stdout"), (stderr, "stderr")):
            if stream is None:
                continue
            thread = threading.Thread(target=self._pump, args=(stream, name), daemon=True)
            thread.start()
            self._readers.append(thread)

        self._timer = threading.Timer(self.timeout, self._on_timeout)
        self._timer.daemon = True
        self._timer.start()
        # 交互式程序的总时长上限：每次输入都能续命，但不能无限续。
        self._hard_deadline = self.started_at + max(60.0, self.timeout * 4)

        threading.Thread(target=self._wait, daemon=True).start()

    def _arm_timer(self, delay: float | None = None) -> None:
        """重设计时器。收到 stdin 输入时调用，把「用户在打字」和「程序卡死」区分开。"""
        if self._timer:
            self._timer.cancel()
        remaining = max(0.5, self._hard_deadline - time.time())
        wait = min(delay if delay is not None else self.timeout, remaining)
        self._timer = threading.Timer(wait, self._on_timeout)
        self._timer.daemon = True
        self._timer.start()

    def _mem_bytes(self) -> int:
        mb = self.mem_limit_mb
        return int(mb) * 1024 * 1024 if mb else MEM_LIMIT_BYTES

    def _on_timeout(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.timed_out = True
            _kill_tree(self.proc.pid)

    def _pump(self, stream, name: str) -> None:
        """按块读，不按行读：`input("提示")` 的提示符没有换行，按行读会卡住。

        stdout 立即转发（提示符要马上出现）；stderr 按行聚合，这样才能把
        traceback 里的临时目录前缀整行替换掉，变成 `File "main.py"`。
        """
        cap = self._limit[name]
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        fd = stream.fileno()
        pending_cr = ""
        buf = ""
        try:
            while True:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                text = decoder.decode(chunk)
                if not text:
                    continue
                if name == "stderr":
                    buf += text
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        self._emit(name, self._strip_workdir(line.rstrip("\r")) + "\n", cap)
                else:
                    text = pending_cr + text
                    pending_cr = ""
                    if text.endswith("\r"):
                        pending_cr = "\r"
                        text = text[:-1]
                    if text:
                        self._emit(name, text.replace("\r\n", "\n"), cap)

            tail = decoder.decode(b"", final=True)
            if name == "stderr":
                buf += tail
                if buf.strip():
                    self._emit(name, self._strip_workdir(buf.rstrip("\r")) + "\n", cap)
            else:
                leftover = pending_cr + tail
                if leftover:
                    self._emit(name, leftover.replace("\r\n", "\n").replace("\r", "\n"), cap)
        finally:
            try:
                stream.close()
            except OSError:
                pass

    def _strip_workdir(self, line: str) -> str:
        """把 `C:\\...\\pytut-run-xxx\\main.py` 收敛成 `main.py`，行号保持不变。"""
        if not self.workdir:
            return line
        return line.replace(self.workdir + os.sep, "").replace(self.workdir, "")

    def _emit(self, name: str, text: str, cap: int) -> None:
        self._bytes[name] += len(text.encode("utf-8", "replace"))
        if self._bytes[name] > cap:
            if not self.truncated:
                self.truncated = True
                self.events.put(
                    (name, f"\n[输出超过 {cap // 1024} KB，后续内容已丢弃]\n")
                )
            return
        self.events.put((name, text))

    def _wait(self) -> None:
        if self.proc is None:
            return
        self.proc.wait()
        for thread in self._readers:
            thread.join(timeout=2)
        if self._timer:
            self._timer.cancel()
        self._close_stdin()
        self.exit_code = self.proc.returncode
        duration = int((time.time() - self.started_at) * 1000)

        self.events.put(
            (
                "done",
                {
                    "exit_code": self.exit_code,
                    "duration_ms": duration,
                    "timed_out": self.timed_out,
                    "truncated": self.truncated,
                },
            )
        )
        self._finished.set()
        close_windows_job(self._job)
        self._job = None
        if self.workdir:
            shutil.rmtree(self.workdir, ignore_errors=True)

    def _close_stdin(self) -> None:
        with self._stdin_lock:
            if self.stdin_closed:
                return
            self.stdin_closed = True
            if self.proc and self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except OSError:
                    pass

    def send(self, text: str) -> bool:
        """把一行输入送进标准输入。返回 False 表示进程已结束。"""
        if self._finished.is_set() or not self.proc or not self.proc.stdin:
            return False
        with self._stdin_lock:
            if self.stdin_closed:
                return False
            try:
                self.proc.stdin.write((text + "\n").encode("utf-8"))
                self.proc.stdin.flush()
            except (BrokenPipeError, ValueError, OSError):
                return False
        self._arm_timer()
        return True

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            _kill_tree(self.proc.pid)

    # ---- 输出流 ----

    def stream(self):
        """把队列转成 SSE 事件序列；客户端断开时由调用方 break。"""
        while True:
            try:
                kind, payload = self.events.get(timeout=20)
            except queue.Empty:
                yield {"type": "ping", "data": {}}
                continue
            if kind == "done":
                yield {"type": "done", "data": payload}
                return
            yield {"type": kind, "data": {"text": str(payload)}}


class RunManager:
    def __init__(self) -> None:
        self._jobs: dict[str, RunJob] = {}
        self._lock = threading.Lock()

    def start(
        self,
        code: str,
        timeout: float | None = None,
        *,
        allow_network: bool = False,
        mem_limit_mb: int | None = None,
    ) -> RunJob:
        try:
            t = float(timeout) if timeout is not None else DEFAULT_TIMEOUT
        except (TypeError, ValueError):
            t = DEFAULT_TIMEOUT
        t = max(0.5, min(t, MAX_TIMEOUT))

        with self._lock:
            alive = [j for j in self._jobs.values() if not j._finished.is_set()]
            if len(alive) >= MAX_CONCURRENT:
                raise RuntimeError(
                    f"同时最多运行 {MAX_CONCURRENT} 段代码，请等当前任务结束"
                )
            job = RunJob(
                code,
                t,
                allow_network=allow_network,
                mem_limit_mb=mem_limit_mb,
            )
            self._jobs[job.id] = job

        job.start()
        return job

    def get(self, run_id: str) -> RunJob | None:
        return self._jobs.get(run_id)

    def stop(self, run_id: str) -> bool:
        job = self._jobs.get(run_id)
        if not job:
            return False
        job.stop()
        return True

    def send(self, run_id: str, text: str) -> bool:
        job = self._jobs.get(run_id)
        if not job:
            return False
        return job.send(text)

    def sweep(self) -> None:
        """清掉已经结束的任务，避免长会话内存缓慢增长。"""
        with self._lock:
            for run_id, job in list(self._jobs.items()):
                if job._finished.is_set():
                    self._jobs.pop(run_id, None)


# 给判题模块复用的公开别名
child_env = _child_env
kill_tree = _kill_tree
