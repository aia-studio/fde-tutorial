+++
id = "s4-87-iterators-advanced"
order = 87
stage = "s4"
official_group = "advanced"
title = "迭代器进阶"
concepts = ["single pass", "reversed", "custom iteration", "iter sentinel"]
prereq = [86]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：reversed"
url = "https://docs.python.org/3/library/functions.html#reversed"

[[doc_refs]]
title = "Language Reference：迭代协议"
url = "https://docs.python.org/3/reference/datamodel.html#iterators"
+++

# 迭代器是一次性的，函数参数尤其如此

第 27 课讲过"迭代器只能走一遍"。这一课把这个知识推进到实战：**函数签名里什么时候该写 Iterable，什么时候该写 Iterator**，以及 `reversed` 为什么比想象中挑剔。

## 迭代器一旦耗尽就永远是空的

```python
def consume(items):
    return list(items)


data = iter([1, 2, 3])
first = consume(data)
second = consume(data)

print(first, second)
```

```expect
[1, 2, 3] []
```

同一个迭代器第二次遍历得到空列表。当函数签名是 `def f(items: Iterator[int])` 时，调用方要明白：**这个函数拥有迭代器，用完就没了**。

这也解释了一个 zip 的经典坑：

```python
zipped = zip([1, 2, 3], ["a", "b", "c"])
print(list(zipped))
print(list(zipped))
```

```expect
[(1, 'a'), (2, 'b'), (3, 'c')]
[]
```

zip 返回的也是迭代器。调试时打印过一次，再用就是空的——变量名的 `zipped` 长得像列表，但不是。

## 两种函数签名的契约

```python
from collections.abc import Iterable, Iterator


def report(items: Iterable[int]) -> None:
    """可以多次遍历：函数内部会先 list() 物化。"""
    values = list(items)
    print(len(values), sum(values))


def stream(items: Iterator[int]) -> None:
    """只遍历一次：数据可能来自无限流。"""
    print(sum(items))


report(iter([1, 2, 3]))
stream(iter([1, 2, 3]))
```

```expect
3 6
6
```

`Iterable` 参数的函数承诺"可以反复遍历"（必要时内部物化）；`Iterator` 参数的函数承诺"只走一遍但省内存"。**签名即契约**——选错了，调用方就会踩到空迭代器。

## `reversed`：不是所有序列都支持

```python
reversed([1, 2, 3])
reversed((1, 2, 3))
reversed("abc")

try:
    reversed(iter([1, 2, 3]))
except TypeError as exc:
    print(type(exc).__name__)
```

```expect
TypeError
```

`reversed` 需要 `__len__` + `__getitem__`（序列），或实现 `__reversed__`。迭代器不能反着走——它只会前进。需要"反着迭代一遍"时，先物化成序列。

```quiz
question = "函数签名写 `items: Iterator[int]`，对调用方意味着什么？"
options = [
  "函数会复制一份，调用方的迭代器不受影响",
  "这个迭代器会被消耗，调用后不能再遍历",
  "函数内部会转成列表并返回",
  "和 Iterable[int] 完全一样"
]
answer = 1
explain = "Iterator 参数 = 所有权转移：函数拥有这个迭代器并用掉它。需要多次遍历的调用方应传列表；想省内存的调用方才传迭代器。签名就是契约。"
```

## 小结

- 迭代器耗尽即空，`zip`/`map`/生成器都一样。
- `Iterable` 参数可反复遍历（内部物化），`Iterator` 参数只走一次。
- `reversed` 只支持序列，迭代器不行。
- 在文档与签名里区分两者，调用方就不会踩空迭代器的坑。
