+++
id = "s2-45-sorting"
order = 45
stage = "s2"
official_group = "moderate"
title = "排序与比较"
concepts = ["sorted", "key", "itemgetter", "stability", "total_ordering"]
prereq = [43]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "HOWTO：排序"
url = "https://docs.python.org/3/howto/sorting.html"

[[doc_refs]]
title = "Library Reference：operator"
url = "https://docs.python.org/3/library/operator.html"
+++

# sorted 一招，key 是全部

`sorted(seq, key=f)` 里 `key` 决定"用什么比"。绝大多数排序难题，答案都是换一个更好的 key，而不是手写比较循环。

## 多级排序：key 返回元组

```python
rows = [("b", 2), ("a", 3), ("a", 1), ("b", 1)]

print(sorted(rows))
print(sorted(rows, key=lambda r: (r[0], r[1])))
print(sorted(rows, key=lambda r: r[1], reverse=True))
```

```expect
[('a', 1), ('a', 3), ('b', 1), ('b', 2)]
[('a', 1), ('a', 3), ('b', 1), ('b', 2)]
[('a', 3), ('b', 2), ('a', 1), ('b', 1)]
```

元组按位置逐个比较，天然支持"先按姓名、再按分数"。**降序与升序混用**时（比如按分数降序、同分按名字升序），`reverse=True` 会把整个 key 反转——这时用"数值取负"技巧：

```python
rows = [("a", 3), ("b", 2), ("a", 1)]
print(sorted(rows, key=lambda r: (-r[1], r[0])))
```

```expect
[('a', 3), ('b', 2), ('a', 1)]
```

## 稳定性：同 key 保持原顺序

```python
data = [("a", 2), ("b", 1), ("a", 1)]
print(sorted(data, key=lambda r: r[1]))
```

```expect
[('b', 1), ('a', 1), ('a', 2)]
```

Python 的排序是**稳定**的：key 相同的元素保持原有相对顺序。两条 "a,2" 与 "a,1" 按分数排后，"a,2" 仍在前（它原本就在前）。稳定排序意味着**可以多次排序叠加**：先按次键排，再按主键排。

## `itemgetter`：比 lambda 快一点、短一点

```python
from operator import itemgetter, attrgetter, mul
from functools import reduce

rows = [("a", 3), ("b", 1)]
print(sorted(rows, key=itemgetter(1)))
print(reduce(mul, [1, 2, 3, 4]))
```

```expect
[('b', 1), ('a', 3)]
24
```

`itemgetter(1)` 等价于 `lambda r: r[1]`，支持多键 `itemgetter(0, 1)`；处理对象属性用 `attrgetter("x", "y")`。

## `total_ordering`：只写两个比较

```python
from functools import total_ordering


@total_ordering
class Version:
    def __init__(self, n):
        self.n = n

    def __eq__(self, other):
        return self.n == other.n

    def __lt__(self, other):
        return self.n < other.n


print(sorted([Version(3), Version(1), Version(2)], key=lambda v: v.n)[0].n)
print(Version(1) <= Version(2))
```

```expect
1
True
```

只实现 `__eq__` 和 `__lt__`，装饰器推导出 `<=`、`>`、`>=`。自己写全六个方法容易漏且不一致，`total_ordering` 是数据模型课（第 25 课 `__eq__`/`__hash__`）的延伸。

```quiz
question = "想「按分数降序，同分按姓名升序」，正确的 key 是？"
options = [
  "lambda r: (r[1], r[0]), reverse=True",
  "lambda r: (-r[1], r[0])",
  "sorted 两次，先姓名后分数",
  "lambda r: r[1] * -1"
]
answer = 1
explain = "reverse=True 会把整个 key 反转，姓名也会倒序。分数取负后用升序，姓名保持自然升序——这是混合方向排序的标准写法。也可以排两次并依赖稳定性。"
```

## 小结

- `key` 返回元组实现多级排序；混用升降序时用"取负"技巧。
- 排序是稳定的：同 key 保持原顺序，多次排序可叠加。
- `itemgetter` / `attrgetter` 替代简单 lambda。
- 数据类需要完整比较时用 `total_ordering`，别手写六个方法。
