+++
id = "s4-85-exceptions-advanced"
order = 85
stage = "s4"
official_group = "advanced"
title = "异常进阶"
concepts = ["ExceptionGroup", "except*", "__notes__", "cancellation"]
prereq = [84]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：ExceptionGroup"
url = "https://docs.python.org/3/library/exceptions.html#exception-groups"

[[doc_refs]]
title = "PEP 654：异常组与 except*"
url = "https://peps.python.org/pep-0654/"
+++

# 一次失败，多个原因

`TaskGroup` 抛出的异常可能包含**多个**失败原因。传统 `except` 只能接一个，于是有了 `ExceptionGroup` 与 `except*`——3.11 引入，为并发而生。

## ExceptionGroup 与 except*

```python
try:
    raise ExceptionGroup(
        "多个问题",
        [ValueError("值不对"), TypeError("类型不对")],
    )
except* ValueError as eg:
    print("值错误：", eg.exceptions[0])
except* TypeError as eg:
    print("类型错误：", eg.exceptions[0])
```

```expect
值错误： 值不对
类型错误： 类型不对
```

`except*` 与普通 `except` 的区别：**每个分支独立检查**，命中的都执行（上面两个分支都跑了）。普通 `except` 命中第一个就停止。注意 `except*` 只能配 ExceptionGroup，普通异常不适用。

## `__notes__`：给异常加备注

```python
try:
    try:
        raise ValueError("原始错误")
    except ValueError as exc:
        exc.add_note("发生在解析配置时")
        raise
except ValueError as exc:
    print(exc)
    print(exc.__notes__)
```

```expect
原始错误
['发生在解析配置时']
```

`add_note` 在异常向上传递的路上补充上下文——中间层知道的细节（哪个文件、哪个配置项）就这么"贴"在异常上，最外层统一打印。

## 异常链的两种方式

```python
try:
    try:
        raise ValueError("根因")
    except ValueError as exc:
        raise RuntimeError("包装") from exc
except RuntimeError as exc:
    print(exc.__cause__ is not None)
    print(exc.__context__ is not None)
```

```expect
True
True
```

- `raise X from exc`：**显式**链（`__cause__`），语义是"这是根因导致的"。
- 在 except 块里直接 `raise X`：**隐式**链（`__context__`），语义是"顺带发生的"。

traceback 对两者都显示，但 `from` 更明确表达意图。**包装异常时永远用 `from`**——这是第 25 课异常链的完整版。

```quiz
question = "`except* ValueError` 与普通 `except ValueError` 的区别是？"
options = [
  "except* 能捕获所有异常类型",
  "except* 针对异常组，多个分支可以各自命中并都执行",
  "except* 性能更好",
  "except* 不需要写异常类型"
]
answer = 1
explain = "except* 逐个分支检查 ExceptionGroup 里的异常，命中的分支都执行（每个分支收到一个「只含匹配异常」的子组）。普通 except 命中第一个分支后其余不再检查。"
```

## 小结

- `ExceptionGroup` 装多个异常，`except*` 分类型独立处理。
- `exc.add_note()` 沿途补充上下文，`__notes__` 随异常传播。
- `raise ... from exc` 显式链（cause）优于隐式链（context）。
- TaskGroup 的失败就是 ExceptionGroup——asyncio 的异常处理离不开它。
