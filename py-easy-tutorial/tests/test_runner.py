"""执行引擎的行为：输出、超时、输出上限、进程树清理。"""

from __future__ import annotations

import time
import unittest

from tutorial.runner import RunManager


def drain(job, limit_seconds: float = 15.0) -> tuple[str, str, dict]:
    """把事件流读干净，返回 (stdout, stderr, done 负载)。"""
    out, err, done = [], [], {}
    deadline = time.time() + limit_seconds
    for event in job.stream():
        if event["type"] == "stdout":
            out.append(event["data"]["text"])
        elif event["type"] == "stderr":
            err.append(event["data"]["text"])
        elif event["type"] == "done":
            done = event["data"]
            break
        if time.time() > deadline:
            break
    return "".join(out), "".join(err), done


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.manager = RunManager()

    def test_stdout_and_exit_code(self):
        job = self.manager.start('print("hello")\nprint(2 + 3)')
        out, err, done = drain(job)
        self.assertEqual(out, "hello\n5\n")
        self.assertEqual(done["exit_code"], 0)
        self.assertFalse(done["timed_out"])

    def test_stderr_is_separate(self):
        job = self.manager.start('import sys\nprint("bad", file=sys.stderr)')
        out, err, done = drain(job)
        self.assertEqual(out, "")
        self.assertIn("bad", err)

    def test_exception_sets_nonzero_exit(self):
        job = self.manager.start("raise ValueError('boom')")
        out, err, done = drain(job)
        self.assertNotEqual(done["exit_code"], 0)
        self.assertIn("ValueError", err)

    def test_infinite_loop_times_out(self):
        started = time.time()
        job = self.manager.start("while True:\n    pass", timeout=1.0)
        out, err, done = drain(job)
        self.assertTrue(done["timed_out"])
        self.assertLess(time.time() - started, 10)

    def test_output_is_capped(self):
        job = self.manager.start("for i in range(200000):\n    print('x' * 20)")
        out, err, done = drain(job)
        self.assertTrue(done["truncated"])
        self.assertLess(len(out), 300_000)

    def test_run_is_isolated_from_repo(self):
        job = self.manager.start("import os\nprint(os.path.basename(os.getcwd()).startswith('pytut-run-'))")
        out, err, done = drain(job)
        self.assertEqual(out.strip(), "True")

    def test_concurrency_limit(self):
        jobs = [self.manager.start("import time\ntime.sleep(1.5)") for _ in range(3)]
        with self.assertRaises(RuntimeError):
            self.manager.start("print(1)")
        for job in jobs:
            drain(job)


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.manager = RunManager()

    def test_traceback_uses_clean_filename(self):
        job = self.manager.start("raise ValueError('boom')")
        out, err, done = drain(job)
        self.assertIn('File "main.py", line 1', err)
        self.assertNotIn("pytut-run-", err)

    def test_stdin_is_interactive(self):
        job = self.manager.start('name = input("名字？ ")\nprint("hi", name)')
        self.assertTrue(job.send("Ada"))
        out, err, done = drain(job)
        self.assertIn("名字？", out)
        self.assertIn("hi Ada", out)
        self.assertEqual(done["exit_code"], 0)

    def test_stdin_eof_when_program_ignores_input(self):
        job = self.manager.start("print('done')")
        out, err, done = drain(job)
        self.assertEqual(out.strip(), "done")
        self.assertFalse(job.send("late"))

    def test_stdin_extends_timeout(self):
        """用户在打字不该被当成死循环杀掉。"""
        job = self.manager.start('name = input()\nprint("got", name)', timeout=3)
        time.sleep(2.2)
        self.assertTrue(job.send("late"))
        out, err, done = drain(job)
        self.assertIn("got late", out)
        self.assertFalse(done["timed_out"])

    def test_external_network_blocked(self):
        job = self.manager.start(
            "import socket\n"
            "s = socket.socket()\n"
            "s.connect(('93.184.216.34', 80))\n"
        )
        out, err, done = drain(job)
        self.assertIn("PermissionError", err)
        self.assertIn("网络访问已被禁用", err)
        self.assertNotEqual(done["exit_code"], 0)

    def test_loopback_allowed(self):
        job = self.manager.start(
            "import socket, threading\n"
            "srv = socket.socket()\n"
            "srv.bind(('127.0.0.1', 0))\n"
            "srv.listen(1)\n"
            "port = srv.getsockname()[1]\n"
            "def accept():\n"
            "    conn, _ = srv.accept()\n"
            "    conn.close()\n"
            "threading.Thread(target=accept, daemon=True).start()\n"
            "c = socket.create_connection(('127.0.0.1', port), timeout=2)\n"
            "print('loopback ok')\n"
            "c.close()\n"
        )
        out, err, done = drain(job)
        self.assertIn("loopback ok", out)
        self.assertEqual(done["exit_code"], 0)

    def test_network_can_be_allowed_per_lesson(self):
        # 只验证 allow_network 会关掉拦截：让代码连一个必定 refused 的本机端口，
        # 期望拿到 ConnectionRefusedError 而不是 PermissionError。
        job = self.manager.start(
            "import socket\n"
            "s = socket.socket()\n"
            "s.settimeout(1)\n"
            "try:\n"
            "    s.connect(('127.0.0.1', 1))\n"
            "except PermissionError:\n"
            "    print('blocked')\n"
            "except OSError as exc:\n"
            "    print(type(exc).__name__)\n",
            allow_network=True,
        )
        out, err, done = drain(job)
        self.assertNotIn("blocked", out)

    def test_memory_limit_kills_runaway_allocation(self):
        job = self.manager.start(
            "buf = bytearray(200 * 1024 * 1024)\nprint(len(buf))",
            mem_limit_mb=64,
        )
        out, err, done = drain(job)
        failed = done["exit_code"] != 0 or "MemoryError" in err
        self.assertTrue(failed, f"未触发内存限制：out={out!r} err={err!r}")
        self.assertNotIn("209715200", out)


if __name__ == "__main__":
    unittest.main()
