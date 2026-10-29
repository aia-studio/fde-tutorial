+++
id = "s4-92-module-getattr"
order = 92
stage = "s4"
official_group = "advanced"
title = "模块级 __getattr__ 与懒加载"
concepts = ["module __getattr__", "lazy import", "deprecation", "__dir__"]
prereq = [91]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "PEP 562：模块的 __getattr__"
url = "https://peps.python.org/pep-0562/"

[[doc_refs]]
title = "Library Reference：module 对象"
url = "https://docs.python.org/3/library/types.html#types.ModuleType"
+++

# 属性不存在时，问模块

类有 `__getattr__`（第 76 课），**模块也有**（3.7 起，PEP 562）。大型库（如 `numpy`、`tensorflow`）的"按需加载子模块"和"访问旧名时发弃用警告"，都建立在这个钩子上。

## 模块级懒加载

```python
import sys
import types

lazy = types.ModuleType("lazy_store")
lazy._data = {"alpha": 1, "beta": 2}


def __getattr__(name):
    if name in lazy._data:
        return lazy._data[name]
    raise AttributeError(f"lazy_store 没有属性 {name}")


lazy.__getattr__ = __getattr__
sys.modules["lazy_store"] = lazy

import lazy_store

print(lazy_store.alpha)
```

```expect
1
```

`alpha` 不是模块的真实属性——访问它触发 `__getattr__`，从 `_data` 里取。真实场景里这一步是 `importlib.import_module("heavy_submodule")`：**import 一个大库的入口模块变得极快**，重资源在首次访问时才加载。

## 弃用路径：旧名发警告

```python
import sys
import types
import warnings

legacy = types.ModuleType("legacy")
legacy._renamed = {"fast_add": "add"}


def __getattr__(name):
    if name in legacy._renamed:
        new_name = legacy._renamed[name]
        warnings.warn(f"{name} 已弃用，请改用 {new_name}", DeprecationWarning, stacklevel=2)
        return getattr(legacy, f"_{new_name}", new_name)
    raise AttributeError(name)


legacy.__getattr__ = __getattr__
sys.modules["legacy"] = legacy

import warnings as _w

with _w.catch_warnings(record=True) as caught:
    _w.simplefilter("always")
    import legacy as _legacy
    _legacy.fast_add

print(len(caught), caught[0].category.__name__)
```

```expect
1 DeprecationWarning
```

旧名字"还能用"，但每次访问都提醒迁移方向——这是大型库（如 `numpy`）平滑过渡 API 的标准手法：**不 breaking，但有明确的时间表**。

> [!tip] 别忘了 __dir__
> `__getattr__` 提供的名字不会出现在 `dir(mod)` 与 IDE 补全里。实现 `__dir__` 返回完整清单，用户体验才完整——"魔法可以被理解"的又一例。

```quiz
question = "模块级 `__getattr__` 与类级 `__getattr__` 的共同点是？"
options = [
  "都在属性常规查找失败后才被调用",
  "都会在每次属性访问时触发",
  "都只能返回字符串",
  "都会自动更新 __dir__"
]
answer = 0
explain = "两者都是兜底钩子：常规查找（真实属性、__dict__、继承链）失败后调用。也因此它们不影响真实属性，且 dir 不会自动包含动态提供的名字。"
```

## 小结

- PEP 562 让模块支持 `__getattr__`，懒加载与弃用提醒的标准实现。
- 懒加载让库的入口 import 变快，重资源按需加载。
- 旧名访问发 DeprecationWarning，给用户迁移时间。
- 配套实现 `__dir__`，否则补全与 dir 不完整。
