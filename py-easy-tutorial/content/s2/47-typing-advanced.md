+++
id = "s2-47-typing-advanced"
order = 47
stage = "s2"
official_group = "moderate"
title = "typing 进阶"
concepts = ["generic", "TypeVar", "Protocol", "Optional", "TypedDict"]
prereq = [46]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：typing"
url = "https://docs.python.org/3/library/typing.html"

[[doc_refs]]
title = "PEP 695：泛型语法"
url = "https://peps.python.org/pep-0695/"
+++

# 注解的进阶形态

三个高频问题，三个对应的进阶工具：「函数的输入输出类型相关」→ 泛型；「这个结构像什么」→ Protocol；「字典的键是什么」→ TypedDict。

## 泛型：PEP 695 的新语法

```python
def first[T](items: list[T]) -> T:
    return items[0]


print(first([1, 2]), first(["a", "b"]))
```

```expect
1 a
```

注意 `first([])` 会抛 `IndexError`——注解不解决运行时问题。但这正是静态检查器的用武之地：mypy 会提示"列表可能为空"，逼你在函数里处理空输入。

`[T]` 声明类型变量，`list[T] -> T` 表达"输入什么元素类型，就返回那种元素"。

老写法需要 `TypeVar`：

```python
from typing import TypeVar

T = TypeVar("T")


def last(items: list[T]) -> T | None:
    return items[-1] if items else None


print(last([1, 2]), last([]))
```

```expect
2 None
```

3.12 之后的代码优先用新语法，老代码库会大量见到 `TypeVar`——两种都要能读懂。

## `X | None`：可空返回值的标准写法

```python
def find_user(uid: int) -> str | None:
    users = {1: "Ada"}
    return users.get(uid)


user = find_user(2)
print(user)
print(user is None)
```

```expect
None
True
```

签名里写着 `str | None`，调用方就知道**必须处理 None 分支**。返回类型从 `str` 改成 `str | None` 是一次破坏性变更，但比让调用方拿到 `None` 再炸要好。

## `Protocol`：结构化子类型

```python
from typing import Protocol


class Speaker(Protocol):
    def speak(self) -> str: ...


class Dog:
    def speak(self) -> str:
        return "汪"


def announce(s: Speaker) -> str:
    return f"它说：{s.speak()}"


print(announce(Dog()))
```

```expect
它说：汪
```

`Dog` **没有继承** `Speaker`，但只要长得像（有 `speak` 方法），静态检查就认为它是 `Speaker`。这是"鸭子类型 + 注解"的组合：不要求显式声明关系，只要求行为匹配——比 ABC 灵活，第 59 课对比两者。

```quiz
question = "`Protocol` 与 `ABC` 的核心区别是？"
options = [
  "Protocol 性能更好",
  "Protocol 是结构化的：不继承、只要求方法形状匹配",
  "ABC 只能用于标准库",
  "Protocol 不能定义方法签名"
]
answer = 1
explain = "ABC 是名义子类型（必须显式继承），Protocol 是结构子类型（长得像就算）。配合 runtime_checkable 还能做 isinstance 检查，但那只检查方法存在性。"
```

## 小结

- `def f[T](x: list[T]) -> T`：新泛型语法，输入输出类型联动。
- `X | None` 强迫调用方处理空值分支，是最值得写的注解。
- `Protocol` 用"形状"代替"继承"，鸭子类型终于有了注解支持。
- 老代码的 `TypeVar` / `Optional[X]` 等价物要能读懂。
