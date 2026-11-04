+++
id = "s2-34-data-model"
order = 34
stage = "s2"
official_group = "moderate"
title = "数据模型入门"
concepts = ["__repr__", "__str__", "__eq__", "__hash__", "dunder"]
prereq = [33]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Language Reference §3：数据模型"
url = "https://docs.python.org/3/reference/datamodel.html"

[[doc_refs]]
title = "Python HOWTOs"
url = "https://docs.python.org/3/howto/index.html"
+++

# 你的对象，Python 怎么“看”它

写 `class Point` 的时候，你只写了 `__init__`。但 `print`、`==`、放进 `set`、`in` 判断——这些操作全都能用。原因是 Python 给每个类都准备了默认行为，而**特殊方法（dunder method）就是改这些默认行为的接口**。

这一课只讲最常用的四个：`__repr__`、`__str__`、`__eq__`、`__hash__`。它们的坑集中在“什么时候必须一起改”。

## 默认的 repr 帮不上忙

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(repr(p).startswith("<__main__.Point object at"))
```

```expect
True
```

`<__main__.Point object at 0x...>` 除了一片内存地址什么信息都没有。调试时你盯着这串字符，唯一能确定的是“它确实是个 Point”。这就是要自己写 `__repr__` 的理由：**repr 是给开发者看的，应当能重建这个对象**。

## `__repr__` 与 `__eq__`：一起写

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x!r}, {self.y!r})"

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)


print(Point(1, 2))
print(Point(1, 2) == Point(1, 2))
print(Point(1, 2) == (1, 2))
```

```expect
Point(1, 2)
True
False
```

两个细节值得停一下：

- `print(p)` 用的是 `__str__`，没定义就回退到 `__repr__`。所以只写 `__repr__` 通常够用。
- `__eq__` 遇到不认识的类型要返回 `NotImplemented`，而不是 `False`。返回 `NotImplemented` 是告诉 Python“我没法判断，你去问对方”，于是 `(1, 2).__eq__(point)` 还有机会接手。

## `__hash__`：一改 `__eq__`，它就被收走了

这是最容易踩的一脚。Python 规定：**定义了 `__eq__` 却没定义 `__hash__`，这个类就变成不可哈希**。

```python
class P:
    def __eq__(self, other):
        return True

try:
    hash(P())
except TypeError as exc:
    print("TypeError:", exc)
```

```expect
TypeError: unhashable type: 'P'
```

原因不难想：哈希和相等必须自洽。如果两个对象“相等”，它们的哈希就必须相同；你自己定了相等规则，解释器就没法替你保证这一点，索性把默认哈希撤掉。

补上它，对象立刻能进 `set` 和 `dict`：

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))


print(len({Point(1, 2), Point(1, 2), Point(3, 4)}))
```

```expect
2
```

> [!warn] 可变对象不要定义 `__hash__`
> 如果 `Point` 之后可能被修改（`p.x = 9`），它就不该可哈希——哈希值变了，`set` 里的位置却不会跟着变，查找会静默失败。不可变对象才配拥有稳定的哈希。这也是 `dataclass(frozen=True)` 才生成 `__hash__` 的原因。

## 四个方法的职责边界

| 方法 | 谁在看 | 该返回什么 | 不写会怎样 |
|---|---|---|---|
| `__repr__` | 开发者、调试器、REPL | 能重建对象的表达式 | 一串内存地址 |
| `__str__` | 最终用户 | 可读文本 | 回退到 `__repr__` |
| `__eq__` | `==`、`in`、`list.remove` | `True` / `False` / `NotImplemented` | 比较身份（`is`） |
| `__hash__` | `set`、`dict` 键 | 整数，且与 `__eq__` 自洽 | 定义 `__eq__` 后变成不可哈希 |

```quiz
question = "一个类只定义了 `__eq__`，没有定义 `__hash__`。把它放进 `set()` 会怎样？"
options = [
  "正常放入，使用默认哈希",
  "抛出 TypeError: unhashable type",
  "放入成功，但之后查找不到",
  "自动改用 id() 作为哈希"
]
answer = 1
explain = "定义 __eq__ 会把 __hash__ 置为 None。此时 hash() 直接抛 TypeError，set 和 dict 都无法使用。需要显式实现 __hash__，并保证与 __eq__ 一致。"
```

## 小结

- 默认 `repr` 只有地址，调试价值为零；写 `__repr__` 是最划算的一笔投入。
- `__eq__` 对不认识的类型返回 `NotImplemented`，不是 `False`。
- 定义 `__eq__` 会顺手把 `__hash__` 撤掉；要进 `set`/`dict` 就得自己补，并保证两者自洽。
- 可变对象不该可哈希。

下一课会看到这些方法背后的统一机制：**属性查找**。`p.x` 到底先查实例还是先查类，答案比“先实例后类”要绕一点。
