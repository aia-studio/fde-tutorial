+++
id = "s4-90-annotations-runtime"
order = 90
stage = "s4"
official_group = "advanced"
title = "注解的运行时"
concepts = ["__annotations__", "get_type_hints", "PEP 649", "annotationlib"]
prereq = [89]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "PEP 649：延迟注解求值"
url = "https://peps.python.org/pep-0649/"

[[doc_refs]]
title = "Library Reference：annotationlib"
url = "https://docs.python.org/3/library/annotationlib.html"
+++

# 注解存哪里、何时求值

第 46 课说过注解是"元数据"。这一课打开引擎盖：它们存在 `__annotations__`，**何时求值**经历了三代变化——而 3.14 的延迟求值改变了所有依赖注解的框架。

## 直接读取

```python
def scale(value: float, factor: float = 2.0) -> float:
    return value * factor


print(scale.__annotations__["value"])
print(scale.__annotations__["return"])
```

```expect
<class 'float'>
<class 'float'>
```

3.14 起，注解默认**延迟求值**（PEP 649）：`__annotations__` 里存的是"求值能力"，首次访问才算。所以这里能拿到真实的类型对象，且定义时不存在的前向引用也不再报错。

## 前向引用：从字符串到自然书写

```python
class Node:
    def connect(self, other: "Node") -> "Node":
        return other


print(Node.connect.__annotations__["other"])
```

```expect
Node
```

过去 `Node` 还没定义完，注解里必须写字符串 `"Node"` 或 `from __future__ import annotations`。延迟求值后直接写类名即可——旧代码里的字符串形式依然合法（字符串原样保留），读旧代码要认识它。

## `get_type_hints` 与框架

```python
import inspect
import typing


def create_user(name: str, age: int, tags: list[str] | None = None) -> dict:
    return {"name": name, "age": age}


hints = typing.get_type_hints(create_user)
print(hints["name"], hints["return"])
print(list(inspect.signature(create_user).parameters))
```

```expect
<class 'str'> <class 'dict'>
['name', 'age', 'tags']
```

框架（FastAPI、pydantic、dataclass）正是靠 `get_type_hints` + `inspect.signature` 读出"参数名、类型、默认值"，然后自动做校验与文档。**你看不见的代码在消费你的注解**——这就是注解生态的运转方式。

```quiz
question = "PEP 649（延迟注解求值）解决的最主要痛点是？"
options = [
  "注解占用了太多磁盘空间",
  "前向引用必须写字符串或用 future 导入，否则 NameError",
  "注解无法被运行时读取",
  "类型检查器速度慢"
]
answer = 1
explain = "过去注解在定义时立即求值，引用尚未定义的类（链表、树、互相引用）必须写字符串。延迟求值把求值推迟到首次访问，前向引用自然成立。"
```

## 小结

- 注解存在 `__annotations__`，3.14 起延迟求值，前向引用免写字符串。
- `get_type_hints` 是框架读取注解的标准入口。
- 字符串形式的旧注解（`"Node"`）依然常见，读代码要认识。
- pydantic / dataclass / FastAPI 都是注解的消费者。
