"""追踪入口：由 tracer.py 以 `trace_main.py <代码路径> <输出路径>` 方式调用。

只有 `__name__ == "__main__"` 时才执行用户代码——这样如果有人在被追踪的代码里
用 multiprocessing，spawn 的子进程重新导入本文件时不会再次执行，避免炸锅。
"""

from __future__ import annotations

import json
import os
import sys
import traceback

MAX_STEPS = 3000
MAX_DEPTH = 40


def _snap(value, depth=0, seen=frozenset()):
    """和 tracer.py 里的同名函数保持一致（拷贝一份避免 import 路径问题）。"""
    if value is None:
        return {"t": "NoneType", "v": "None"}
    if isinstance(value, bool):
        return {"t": "bool", "v": str(value)}
    if isinstance(value, int):
        return {"t": "int", "v": str(value)}
    if isinstance(value, float):
        return {"t": "float", "v": repr(value)}
    if isinstance(value, str):
        return {"t": "str", "v": value if len(value) <= 60 else value[:57] + "...", "q": True}
    if isinstance(value, bytes):
        return {"t": "bytes", "v": repr(value)[:60]}

    t = type(value).__name__

    if isinstance(value, (list, tuple, set, frozenset, dict)):
        if id(value) in seen or depth >= 2:
            return {"t": t, "v": "…", "oid": id(value)}
        seen2 = seen | {id(value)}
        if isinstance(value, dict):
            items = [
                [_snap(k, depth + 1, seen2), _snap(v, depth + 1, seen2)]
                for k, v in list(value.items())[:20]
            ]
            more = len(value) - len(items)
            if more > 0:
                items.append([{"t": "…", "v": f"还有 {more} 项"}])
            return {"t": "dict", "oid": id(value), "items": items}
        if isinstance(value, (set, frozenset)):
            members = sorted(repr(x) for x in list(value)[:20])
            return {"t": t, "v": "{" + ", ".join(members) + "}", "oid": id(value)}
        items = [_snap(x, depth + 1, seen2) for x in list(value)[:20]]
        return {"t": t, "oid": id(value), "items": items}

    if callable(value):
        return {"t": "callable", "v": str(getattr(value, "__qualname__", t))}

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

    return {"t": t, "v": repr(value)[:60], "oid": id(value)}


def main(argv):
    if os.environ.get("PYTUT_TRACE_ENTRY") != "1":
        return 1
    if len(argv) < 3:
        return 1

    code_path, out_path = argv[1], argv[2]
    with open(code_path, encoding="utf-8") as fh:
        source = fh.read()

    code = compile(source, "main.py", "exec")

    steps: list[dict] = []
    counter = {"n": 0}

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != "main.py":
            return None
        depth = 0
        fr = frame
        while fr.f_back is not None:
            fr = fr.f_back
            depth += 1
        if depth > MAX_DEPTH:
            return None
        if counter["n"] >= MAX_STEPS:
            return None

        if event not in ("line", "return", "exception"):
            return tracer

        counter["n"] += 1

        stack = []
        fr = frame
        while fr is not None and fr.f_code.co_filename == "main.py":
            stack.append(fr.f_code.co_name)
            fr = fr.f_back
        stack.reverse()

        step = {
            "i": counter["n"],
            "event": event,
            "line": frame.f_lineno,
            "func": frame.f_code.co_name,
            "stack": stack,
            "locals": {
                name: _snap(value)
                for name, value in frame.f_locals.items()
                if not name.startswith("__")
            },
        }
        if event == "exception" and isinstance(arg, tuple) and arg[1] is not None:
            step["exc"] = f"{type(arg[1]).__name__}: {arg[1]}"
        steps.append(step)
        return tracer

    namespace = {
        "__name__": "__main__",
        "__file__": code_path,
        "__builtins__": __builtins__,
    }

    exit_code = 0
    error = None
    sys.settrace(tracer)
    try:
        exec(code, namespace)
    except BaseException:
        exit_code = 1
        error = traceback.format_exc(limit=8).strip()
    finally:
        sys.settrace(None)

    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(
            {"steps": steps, "exit_code": exit_code, "error": error},
            fh,
            ensure_ascii=False,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
