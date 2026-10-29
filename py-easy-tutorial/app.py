#!/usr/bin/env python3
"""交互式 Python 教程 · 启动器。

    python app.py                # 自动选端口并打开浏览器
    python app.py --port 8800    # 指定端口
    python app.py --no-browser   # 不自动开浏览器

最低 Python 3.15：低于这个版本直接退出，不做降级运行。
"""

from __future__ import annotations

import argparse
import sys

from tutorial import MIN_PYTHON, __version__

_NEED = ".".join(str(p) for p in MIN_PYTHON)
_HAVE = ".".join(str(p) for p in sys.version_info[:3])


def _version_banner() -> str:
    return f"""
  这个教程要求 Python {_NEED} 或更高版本，当前解释器是 {_HAVE}。

  它用了 3.15 的语法和标准库，在老解释器上跑起来只会得到一半正确、
  一半报错的结果，所以这里直接停下，而不是带着你调试环境问题。

  请用装好的 3.15 启动，例如：

      conda activate pytest
      python app.py

  或者用完整路径指定 3.15 的解释器：

      C:\\path\\to\\python3.15\\python.exe app.py

  安装 3.15：https://www.python.org/downloads/
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="app.py", description="交互式 Python 教程（本地运行）"
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="端口，默认自动选择")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--version", action="version", version=f"py-tutorial {__version__}")
    args = parser.parse_args()

    if sys.version_info < MIN_PYTHON:
        sys.stderr.write(_version_banner())
        return 2

    from tutorial.server import main as serve

    try:
        serve(args.host, args.port, open_browser=not args.no_browser)
    except OSError as exc:
        sys.stderr.write(f"\n  启动失败：{exc}\n  端口可能被占用，试试 --port 8800\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
