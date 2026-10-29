"""二期扩展：接入评估、权限收窄、索引升级与方案汇总。

运行（在 src/ 下）：
    python -m ch07.intake
    python -m ch07.tenancy
    python -m ch07.upgrade
    python -m ch07.report

包级导出按需加载，`python -m ch07.intake` 不会因为包初始化而重复导入子模块。
"""

from importlib import import_module

_EXPORTS = {
    "Request": "ch07.intake",
    "REQUESTS": "ch07.intake",
    "evaluate": "ch07.intake",
    "Chunk": "ch07.tenancy",
    "Ctx": "ch07.tenancy",
    "visible": "ch07.tenancy",
    "retrieve": "ch07.tenancy",
    "build": "ch07.upgrade",
    "search": "ch07.upgrade",
    "metrics": "ch07.upgrade",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module 'ch07' has no attribute {name!r}")
    return getattr(import_module(_EXPORTS[name]), name)
