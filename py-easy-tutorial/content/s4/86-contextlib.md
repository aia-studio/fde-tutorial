+++
id = "s4-86-contextlib"
order = 86
stage = "s4"
official_group = "advanced"
title = "contextlib 全家桶"
concepts = ["ExitStack", "redirect_stdout", "closing", "reentrant"]
prereq = [85]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：contextlib"
url = "https://docs.python.org/3/library/contextlib.html"

[[doc_refs]]
title = "Library Reference：ExitStack"
url = "https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack"
+++

# contextmanager 之外的四件武器

`@contextmanager` 是最常用的，但 contextlib 还有几件解决"特殊形状问题"的工具：动态数量的资源（ExitStack）、捕获输出（redirect_stdout）、只要收尾（closing）。

## ExitStack：数量不定的资源

```python
from contextlib import ExitStack

files = ["a.txt", "b.txt"]

with ExitStack() as stack:
    handles = [
        stack.enter_context(open(name, "w", encoding="utf-8"))
        for name in files
    ]
    for handle in handles:
        handle.write("x")

print("两个文件都已写入并关闭")
```

```expect
两个文件都已写入并关闭
```

`with open(...) as f1, open(...) as f2:` 写法在文件数量**固定**时可用；数量运行时才知道，就该用 `ExitStack` 动态压栈，退出时按**后进先出**自动关闭。

## `redirect_stdout`：捕获第三方库的输出

```python
import io
from contextlib import redirect_stdout

buffer = io.StringIO()

with redirect_stdout(buffer):
    print("这行不会出现在控制台")

print("抓到：", buffer.getvalue().strip())
```

```expect
抓到： 这行不会出现在控制台
```

有些库固执地用 `print` 而不是 logging——`redirect_stdout` 把它"骗"到你的缓冲区里。同族的 `redirect_stderr`、`suppress`（第 39 课）是同门。

## `closing`：只有 close 没有 with 的对象

```python
from contextlib import closing


class Connection:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


with closing(Connection()) as conn:
    print("使用连接：", not conn.closed)

print("连接已关闭：", conn.closed)
```

```expect
使用连接： True
连接已关闭： True
```

Some 对象有 `close()` 却没实现上下文协议——`closing()` 给它包一层，退出时自动调 `close()`。不用为了用 with 而去改别人的类。

```quiz
question = "`ExitStack` 与多个 `with` 语句（`with a as f1, b as f2:`）的核心区别是？"
options = [
  "ExitStack 更快",
  "ExitStack 支持运行时才知道数量的资源，按后进先出收尾",
  "ExitStack 可以吞异常",
  "没有区别，只是写法不同"
]
answer = 1
explain = "逗号连接的 with 数量在写代码时固定；ExitStack 用循环 enter_context 动态压栈，且退出顺序严格后进先出——与嵌套 with 的语义完全一致。"
```

## 小结

- `ExitStack` 处理"数量运行时才知道"的资源，LIFO 收尾。
- `redirect_stdout/stderr` 捕获不守规矩的第三方输出。
- `closing()` 让只有 `close()` 的对象接入 with。
- `@contextmanager` 产出的管理器**不可复用**，重复 with 需重新调用工厂。
