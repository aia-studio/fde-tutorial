"""收尾与知识转移：终验证据、交接演练、需求边界。

运行（在 src/ 下）：
    python -m ch08.signoff
    python -m ch08.handover
    python -m ch08.boundary

包级导出按需加载，`python -m ch08.signoff` 不会因为包初始化而重复导入子模块。
"""

from importlib import import_module

_EXPORTS = {
    "Item": "ch08.signoff",
    "ITEMS": "ch08.signoff",
    "blocked": "ch08.signoff",
    "apply_fixes": "ch08.signoff",
    "Drill": "ch08.handover",
    "DRILLS": "ch08.handover",
    "after_patch": "ch08.handover",
    "Ask": "ch08.boundary",
    "ASKS": "ch08.boundary",
    "classify": "ch08.boundary",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module 'ch08' has no attribute {name!r}")
    return getattr(import_module(_EXPORTS[name]), name)
