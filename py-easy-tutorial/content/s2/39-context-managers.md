+++
id = "s2-39-context-managers"
order = 39
stage = "s2"
official_group = "moderate"
title = "上下文管理器"
concepts = ["with", "__enter__", "__exit__", "contextmanager", "suppress"]
prereq = [38]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：with 语句"
url = "https://docs.python.org/3/reference/compound_stmts.html#with"

[[doc_refs]]
title = "Library Reference：contextlib"
url = "https://docs.python.org/3/library/contextlib.html"
+++

# 不管成不成功，收尾都要做

打开要关、锁要放、临时目录要删、事务要提交或回滚——这类"成对操作"散落在代码里迟早漏一半。`with` 把收尾逻辑固定在协议里，**异常路径也逃不掉**。

## 实现一个上下文管理器

```python
class Tracer:
    def __enter__(self):
        print("进入")
        return self

    def __exit__(self, exc_type, exc, tb):
        print("退出，异常类型：", exc_type.__name__ if exc_type else "无")
        return False


with Tracer() as t:
    print("干活中")
```

```expect
进入
干活中
退出，异常类型： 无
```

`__enter__` 的返回值交给 `as` 后面的变量；`__exit__` 无论块内是否抛异常都会执行，四个收尾参数一个不落。

## 异常路径也逃不掉

```python
class Guard:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        print("清理（异常也走这里）")
        return False


try:
    with Guard():
        raise ValueError("炸了")
except ValueError as exc:
    print("外面捕获：", exc)
```

```expect
清理（异常也走这里）
外面捕获： 炸了
```

`__exit__` 返回 `False`（或 None）表示"不吞异常"，异常继续往外抛；返回 `True` 才表示"我处理完了"。**默认写 False 是安全姿势**——不明确要抑制异常时，永远不要返回 True。

## `@contextmanager`：生成器的快捷写法

```python
from contextlib import contextmanager


@contextmanager
def tag(name):
    print(f"<{name}>")
    yield
    print(f"</{name}>")


with tag("h1"):
    print("标题内容")
```

```expect
<h1>
标题内容
</h1>
```

`yield` 之前是 `__enter__`，之后是 `__exit__`，`yield` 的值给 `as`。大多数自定义上下文管理器用这个写法就够，比手写类短一半。

## `suppress`：精确吞掉已知异常

```python
from contextlib import suppress

with suppress(FileNotFoundError):
    open("不存在的文件.txt", encoding="utf-8")

print("继续执行")
```

```expect
继续执行
```

`suppress(FileNotFoundError)` 等价于 try/except 该异常，但**声明式**且范围只限这个块。比裸 `try: ... except FileNotFoundError: pass` 更能表达意图。

```quiz
question = "`__exit__` 返回 `True` 意味着什么？"
options = [
  "资源已成功释放",
  "块内没有发生异常",
  "异常已被处理，不再向外抛出",
  "with 块会再执行一次"
]
answer = 2
explain = "__exit__ 的返回值只回答一个问题：这个异常是否算「已处理」。返回 True 会吞掉异常，调用方完全不知情——没有把握时返回 False/None。"
```

## 小结

- `with` 保证 `__exit__` 一定执行，异常路径也不例外。
- `__exit__` 返回 True 会吞异常，默认返回 False。
- `@contextmanager` 用生成器写收尾逻辑，`yield` 前后对应进出。
- `suppress(具体异常)` 表达"我知道并接受这个失败"，比裸 try 更清晰。
