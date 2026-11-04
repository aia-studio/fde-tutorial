"""本地 HTTP 服务：静态资源 + 课程 API + 代码执行（SSE 流式输出）。

只用标准库。SSE 而非 WebSocket，是因为它足够、且浏览器端 `EventSource` 自带重连，
不需要在客户端写心跳与状态机。
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from tutorial import __version__
from tutorial.grader import grade
from tutorial.limits import memory_limit_supported
from tutorial.progress import ProgressStore
from tutorial.runner import MAX_TIMEOUT, RunManager
from tutorial.tracer import trace as run_trace

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DATA = WEB / "data"

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

CHECK_SEMAPHORE = threading.BoundedSemaphore(3)


class Handler(BaseHTTPRequestHandler):
    server_version = f"PyTutorial/{__version__}"
    protocol_version = "HTTP/1.0"

    manager: RunManager
    store: ProgressStore
    quiet: bool = False

    # ---- 基础工具 ----

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        if not self.quiet:
            sys.stderr.write("  %s\n" % (fmt % args))

    def _send_json(self, payload: object, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    # ---- 路由 ----

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path == "/api/health":
            self._send_json(
                {
                    "app": "interactive-python-tutorial",
                    "version": __version__,
                    "python": sys.version.split()[0],
                    "supported": True,
                    "max_timeout": MAX_TIMEOUT,
                    "capabilities": {
                        "threads": True,
                        "processes": True,
                        "network": True,
                        "fs_write": True,
                        "stdin": True,
                        "memory_limit": memory_limit_supported(),
                    },
                }
            )
            return

        if path == "/api/lessons":
            self._serve_data("index.json")
            return

        if path == "/api/progress":
            self._send_json(self.store.load())
            return

        if path.startswith("/api/lessons/"):
            lesson_id = unquote(path[len("/api/lessons/") :])
            if not lesson_id or "/" in lesson_id or "\\" in lesson_id or ".." in lesson_id:
                self._error(HTTPStatus.BAD_REQUEST, "非法的课程 id")
                return
            self._serve_data(f"lessons/{lesson_id}.json")
            return

        if path.startswith("/api/stream/"):
            self._stream(path[len("/api/stream/") :])
            return

        self._serve_static(path)

    def do_HEAD(self) -> None:  # noqa: N802
        """预览面板会先发 HEAD 探测端口，不回这个会导致启动判定失败。"""
        path = urlparse(self.path).path
        rel = "index.html" if path in ("/", "") else unquote(path).lstrip("/")
        target = (WEB / rel).resolve()
        if str(target).startswith(str(WEB.resolve())) and target.is_file():
            ctype, _ = mimetypes.guess_type(str(target))
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path == "/api/check":
            self._handle_check()
            return

        if path == "/api/trace":
            self._handle_trace()
            return

        if path == "/api/run":
            payload = self._read_json()
            code = payload.get("code")
            if not isinstance(code, str) or not code.strip():
                self._error(HTTPStatus.BAD_REQUEST, "code 不能为空")
                return
            if len(code) > 200_000:
                self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "代码过长")
                return
            try:
                job = self.manager.start(
                    code,
                    payload.get("timeout"),
                    allow_network=bool(payload.get("allow_network")),
                )
            except RuntimeError as exc:
                self._error(HTTPStatus.TOO_MANY_REQUESTS, str(exc))
                return
            self._send_json(
                {
                    "run_id": job.id,
                    "timeout": job.timeout,
                    "stream": f"/api/stream/{job.id}",
                }
            )
            return

        if path.startswith("/api/run/") and path.endswith("/stdin"):
            run_id = path[len("/api/run/") : -len("/stdin")]
            payload = self._read_json()
            data = payload.get("data")
            if not isinstance(data, str):
                self._error(HTTPStatus.BAD_REQUEST, "data 必须是字符串")
                return
            if len(data) > 4096:
                self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "单行输入过长")
                return
            sent = self.manager.send(run_id, data)
            self._send_json(
                {"sent": sent}, HTTPStatus.OK if sent else HTTPStatus.CONFLICT
            )
            return

        if path.startswith("/api/run/") and path.endswith("/stop"):
            run_id = path[len("/api/run/") : -len("/stop")]
            ok = self.manager.stop(run_id)
            self._send_json({"stopped": ok}, HTTPStatus.OK if ok else HTTPStatus.NOT_FOUND)
            return

        self._error(HTTPStatus.NOT_FOUND, "未知接口")

    def do_PUT(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/progress":
            self._error(HTTPStatus.NOT_FOUND, "未知接口")
            return
        payload = self._read_json()
        try:
            saved = self.store.save(payload)
        except ValueError as exc:
            self._error(HTTPStatus.BAD_REQUEST, f"进度格式不合法：{exc}")
            return
        self._send_json(saved)

    # ---- 判题 ----

    def _handle_check(self) -> None:
        payload = self._read_json()
        lesson_id = payload.get("lesson_id")
        exercise_id = payload.get("exercise_id")
        code = payload.get("code")

        if not isinstance(lesson_id, str) or not isinstance(exercise_id, str):
            self._error(HTTPStatus.BAD_REQUEST, "缺少 lesson_id 或 exercise_id")
            return
        if not isinstance(code, str) or not code.strip():
            self._error(HTTPStatus.BAD_REQUEST, "代码不能为空")
            return
        if len(code) > 100_000:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "代码过长")
            return
        if "/" in lesson_id or ".." in lesson_id:
            self._error(HTTPStatus.BAD_REQUEST, "非法的 lesson_id")
            return

        block = self._find_exercise(lesson_id, exercise_id)
        if block is None:
            self._error(HTTPStatus.NOT_FOUND, "找不到这道练习")
            return

        if not CHECK_SEMAPHORE.acquire(timeout=2):
            self._error(HTTPStatus.TOO_MANY_REQUESTS, "判题队列已满，稍后再试")
            return
        try:
            result = grade(code, block["tests"], timeout=10.0)
        finally:
            CHECK_SEMAPHORE.release()

        self._send_json(
            {
                "passed": result["passed"],
                "results": result["results"],
                "timed_out": result["timed_out"],
                "stderr": result["stderr"][-2000:],
                "xp": block.get("xp", 10),
            }
        )

    # ---- 单步追踪 ----

    def _handle_trace(self) -> None:
        payload = self._read_json()
        code = payload.get("code")
        if not isinstance(code, str) or not code.strip():
            self._error(HTTPStatus.BAD_REQUEST, "code 不能为空")
            return
        if len(code) > 40_000:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "step 块的代码过长")
            return
        if code.count("\n") > 60:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "step 块最多 40 行代码")
            return

        if not CHECK_SEMAPHORE.acquire(timeout=2):
            self._error(HTTPStatus.TOO_MANY_REQUESTS, "追踪队列已满，稍后再试")
            return
        try:
            result = run_trace(code, timeout=10.0)
        finally:
            CHECK_SEMAPHORE.release()

        self._send_json(result)

    def _find_exercise(self, lesson_id: str, exercise_id: str) -> dict | None:
        path = DATA / "lessons" / f"{lesson_id}.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        for block in data.get("blocks", []):
            if block.get("type") == "exercise" and block.get("id") == exercise_id:
                return block
        return None

    # ---- 静态资源 ----

    def _serve_data(self, relative: str) -> None:
        target = (DATA / relative).resolve()
        if not str(target).startswith(str(DATA.resolve())) or not target.is_file():
            self._error(HTTPStatus.NOT_FOUND, "还未生成课程数据，先运行 python build.py")
            return
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str) -> None:
        if path in ("/", ""):
            path = "/index.html"
        rel = unquote(path).lstrip("/")
        target = (WEB / rel).resolve()
        if not str(target).startswith(str(WEB.resolve())) or not target.is_file():
            self._error(HTTPStatus.NOT_FOUND, f"找不到 {path}")
            return

        body = target.read_bytes()
        ctype, _ = mimetypes.guess_type(str(target))
        ctype = ctype or "application/octet-stream"
        if ctype.startswith("text/") or ctype in (
            "application/javascript",
            "application/json",
            "image/svg+xml",
        ):
            ctype += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---- SSE ----

    def _stream(self, run_id: str) -> None:
        job = self.manager.get(run_id)
        if job is None:
            self._error(HTTPStatus.NOT_FOUND, "运行记录不存在或已过期")
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.close_connection = True

        try:
            self.wfile.write(b"event: open\ndata: {}\n\n")
            self.wfile.flush()
            for event in job.stream():
                chunk = (
                    f"event: {event['type']}\n"
                    f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
                ).encode("utf-8")
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            job.stop()
        finally:
            self.manager.sweep()


def serve(host: str = "127.0.0.1", port: int = 0, *, open_browser: bool = True, quiet: bool = False) -> ThreadingHTTPServer:
    handler = type(
        "BoundHandler",
        (Handler,),
        {
            "manager": RunManager(),
            "store": ProgressStore(ROOT / ".data" / "progress.json"),
            "quiet": quiet,
        },
    )
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    actual_port = httpd.server_address[1]
    url = f"http://{host}:{actual_port}/"

    if not quiet:
        print("\n  交互式 Python 教程")
        print(f"  {url}")
        print(f"  Python {sys.version.split()[0]} · 按 Ctrl+C 停止\n")

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    return httpd


def main(host: str = "127.0.0.1", port: int = 0, *, open_browser: bool = True) -> None:
    httpd = serve(host, port, open_browser=open_browser)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止。")
    finally:
        httpd.shutdown()
        httpd.server_close()
