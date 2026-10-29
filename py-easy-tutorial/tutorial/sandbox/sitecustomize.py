"""子解释器启动时安装的护栏。

靠 `PYTHONPATH` 指向本目录，让 CPython 启动时自动导入 `sitecustomize`。
这样不需要在用户代码前面插入任何一行，行号保持 1:1，traceback 直接可用。

只拦"真正出网"的 connect：回环地址放行，否则 multiprocessing 之类依赖本机
socket 的东西会被误伤。
"""

from __future__ import annotations

import os
import socket

_ALLOW = os.environ.get("PYTUT_ALLOW_NETWORK") == "1"
_INSTALLED = False

_MESSAGE = (
    "网络访问已被禁用：教程默认不允许课程代码连接外部主机。"
    "如果这一节确实需要联网，请在课程 front matter 里设置 allow_network = true。"
)

_LOCAL_HOSTS = {"", "localhost", "::1", "0.0.0.0"}


def _is_loopback(address: object) -> bool:
    host = ""
    if isinstance(address, tuple) and address:
        host = address[0]
    elif isinstance(address, str):
        host = address
    if not isinstance(host, str):
        return False
    return host in _LOCAL_HOSTS or host.startswith("127.") or host.startswith("::ffff:127.")


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded_connect(self, address, *args, **kwargs):
        if not _is_loopback(address):
            raise PermissionError(_MESSAGE)
        return original_connect(self, address, *args, **kwargs)

    def guarded_connect_ex(self, address, *args, **kwargs):
        if not _is_loopback(address):
            raise PermissionError(_MESSAGE)
        return original_connect_ex(self, address, *args, **kwargs)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex


if not _ALLOW:
    _install()
