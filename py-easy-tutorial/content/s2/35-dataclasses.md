+++
id = "s2-35-dataclasses"
order = 35
stage = "s2"
official_group = "moderate"
title = "dataclasses"
concepts = ["dataclass", "frozen", "field", "default_factory", "eq"]
prereq = [34]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：dataclasses"
url = "https://docs.python.org/3/library/dataclasses.html"

[[doc_refs]]
title = "PEP 557：dataclasses"
url = "https://peps.python.org/pep-0557/"
+++

# 把样板代码交给解释器

手写一个数据类需要 `__init__`、`__repr__`、`__eq__` 三个方法，全是一眼能看出"该长什么样"的样板代码。`@dataclass` 把它们生成出来，你只声明字段。

## 三行顶三屏

```python
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


p = Point(1, 2)
print(p)
print(p == Point(1, 2))
print(p.x)
```

```expect
Point(x=1, y=2)
True
1
```

`@dataclass` 根据 `x: int` 这样的注解生成：`__init__(self, x, y)`、可读的 `__repr__`、按字段比较的 `__eq__`。**没有注解的字段会被忽略**——类型写的是文档，也是生成器的工作依据。

## frozen：不可变数据类

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str
    port: int


c = Config("localhost", 5432)
print(c.host, c.port)

try:
    c.port = 1
except Exception as exc:
    print(type(exc).__name__)
```

```expect
localhost 5432
FrozenInstanceError
```

`frozen=True` 除了禁止修改，还会生成 `__hash__`——所以 frozen 实例能进 `set`、当 `dict` 的键（第 25 课讲过：定义了 `__eq__` 却不可哈希的坑，这里被正确处理了）。

## 默认值与可变字段

```python
from dataclasses import dataclass, field


@dataclass
class Bag:
    owner: str
    items: list = field(default_factory=list)


a = Bag("Ada")
a.items.append("球")
b = Bag("Bob")

print(a.items, b.items)
print(a)
```

```expect
['球'] []
Bag(owner='Ada', items=['球'])
```

`field(default_factory=list)` 是第 15 课"可变默认参数"在类里的正解。直接写 `items: list = []` 会抛 `ValueError`——dataclass 直接禁止了这种写法，比裸函数严格。

> [!tip] 什么时候用 dataclass
> 字段大于等于两个、且类的主要职责是"装数据"（配置项、记录、返回值）——就上 `@dataclass`。行为复杂的类（一堆方法）才手写 `__init__`。

```quiz
question = "`@dataclass` 会自动生成下面哪一个方法？"
options = ["__new__", "__repr__", "__hash__（默认情况）", "__getattr__"]
answer = 1
explain = "默认生成 __init__/__repr__/__eq__。__hash__ 只有在 frozen=True（或 eq=False）时才生成；默认可变对象不可哈希，避免进 set 后修改导致查找失败。"
```

## 小结

- `@dataclass` 按字段注解生成 `__init__` / `__repr__` / `__eq__`。
- `frozen=True` 禁止修改，并让实例可哈希。
- 可变字段用 `field(default_factory=list)`，禁止裸 `[]`。
- "装数据"的类优先 dataclass，行为复杂的类才手写。
