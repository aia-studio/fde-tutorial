+++
id = "s4-84-import-system"
order = 84
stage = "s4"
official_group = "advanced"
title = "导入系统深入"
concepts = ["finder", "loader", "importlib", "circular import", "__all__"]
prereq = [83]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference：导入系统"
url = "https://docs.python.org/3/reference/import.html"

[[doc_refs]]
title = "Library Reference：importlib"
url = "https://docs.python.org/3/library/importlib.html"
+++

# `import` 的四步旅程

`import foo` 做了四件事：查缓存（`sys.modules`）→ 找到模块（finder）→ 加载并执行（loader）→ 绑定名字。理解这四步，循环导入、`--only` 之外的一切导入怪象都有解。

## `sys.modules` 是缓存，也是注册表

```python
import sys
import types

mod = types.ModuleType("demo")
mod.value = 42
sys.modules["demo"] = mod

import demo

print(demo.value)
```

```expect
42
```

把一个模块对象塞进 `sys.modules` 后，`import demo` 直接命中缓存——**根本不会去找文件**。这个技巧是"运行时注入模块"的基础（测试里 mock 整个模块就是这么干的）。

## finder/loader：谁去找、谁来装

```python
import importlib.util

spec = importlib.util.find_spec("json")
print(spec.name)
print(spec.origin.endswith("__init__.py"))
```

```expect
json
True
```

`find_spec` 返回模块的"规格说明"：名字、来源路径、加载器。`sys.meta_path` 里的 finder 依次询问"这个模块你认识吗"，找到后交给对应 loader 执行。第 70 课的"导入系统深入"查源码路径，本质就是读 spec。

## 循环导入：为什么会发生

```python
# a.py 的内容：
#     import b
#     X = 1
#
# b.py 的内容：
#     import a          ← 此刻 a 模块只执行到第一行，X 还不存在
#     Y = a.X           ← AttributeError 或 ImportError
```

导入 `a` 时，Python 把半成品 `a` 放进 `sys.modules`，开始执行顶层代码；第一行 `import b` 触发导入 `b`，而 `b` 又要读 `a.X`——此刻 `a` 还没执行到 `X = 1`。**循环导入的报错点永远在"半成品属性"上**，修复方向都是把"定义"与"使用"错开：

- 把 `import` 移到函数内部（用到才导入）；
- 把共享常量抽到第三个模块，双方都导入它；
- 重构层级，让依赖变成单向。

## `__all__`：`import *` 的白名单

```python
import sys
import types

_demo = types.ModuleType("demo_pkg")
_demo.__dict__["__all__"] = ["public_api"]
_demo.__dict__["public_api"] = lambda: "公开"
_demo.__dict__["_private"] = lambda: "私有"
sys.modules["demo_pkg"] = _demo

from demo_pkg import *  # noqa: F403
print("public_api" in globals())
print(_demo.__all__)
print(_demo._private())
```

```expect
True
['public_api']
私有
```

`__all__` 只约束 `import *` 的行为，**不影响普通导入**——`_private` 依然可以显式导入。它是"这是公共接口"的声明，不是访问控制。

```quiz
question = "出现 `ImportError: cannot import name 'X' from partially initialized module`，最可能的原因是？"
options = [
  "模块文件不存在",
  "循环导入：两个模块互相 import，读取了半成品模块的属性",
  "Python 版本不支持该语法",
  "模块名与内置模块重名"
]
answer = 1
explain = "partially initialized 说明导入发生在对方顶层代码执行完毕之前。修复方向：局部导入、抽出共享常量模块、或理顺依赖方向让图变成无环。"
```

## 小结

- `import` = 查 `sys.modules` 缓存 → finder 找 → loader 执行 → 绑定名字。
- 往 `sys.modules` 塞模块对象，可以"伪造"一个可导入的模块。
- 循环导入的报错点是"半成品属性"，修复靠打破环。
- `__all__` 只管 `import *`，不是访问控制。
