+++
id = "s2-42-itertools"
order = 42
stage = "s2"
official_group = "moderate"
title = "itertools"
concepts = ["itertools", "chain", "islice", "groupby", "combinations"]
prereq = [40]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：itertools"
url = "https://docs.python.org/3/library/itertools.html"

[[doc_refs]]
title = "HOWTO：itertools 配方"
url = "https://docs.python.org/3/library/itertools.html#itertools-recipes"
+++

# 迭代器的乐高块

itertools 全部是**惰性**的、用 C 实现的迭代器工具。组合起来能表达复杂的流处理，速度接近手写循环，代码只有一行。

## chain 与 islice：拼接与切片

```python
from itertools import chain, islice, count

print(list(chain([1, 2], [3], "ab")))
print(list(islice(count(10), 3)))
```

```expect
[1, 2, 3, 'a', 'b']
[10, 11, 12]
```

`chain` 把多个可迭代对象串成一条流（注意字符串也被逐字符遍历）；`count(10)` 是**无限**计数器，`islice` 从中切出前 3 个——无限流必须配 islice 或提前 break，否则死循环。

## groupby：按 key 分组（要先排序）

```python
from itertools import groupby

words = ["apple", "avocado", "banana", "blueberry"]
groups = {k: list(g) for k, g in groupby(sorted(words), key=lambda w: w[0])}

print(sorted(groups.items()))
```

```expect
[('a', ['apple', 'avocado']), ('b', ['banana', 'blueberry'])]
```

`groupby` 只对**相邻**的相同键分组——不排序就会漏组。这是它最容易踩的坑，也是最常被忽略的文档细节。

## 组合与排列

```python
from itertools import combinations, product, permutations

print(list(combinations("AB", 2)))
print(list(product([0, 1], repeat=2)))
print(len(list(permutations("ABC"))))
```

```expect
[('A', 'B')]
[(0, 0), (0, 1), (1, 0), (1, 1)]
6
```

三个函数的语义要分清：`combinations` 组合（不管顺序）、`permutations` 排列（管顺序）、`product` 笛卡尔积（可重复）。

> [!tip] 无限流 + islice 是标准姿势
> `count` / `cycle` / `repeat` 都是无限迭代器。配合 `islice` 或 `zip(..., range(n))` 截断，可以写出"取前 N 个满足条件的"这类逻辑而不用手写计数器。

```quiz
question = "直接 `list(groupby(words))` 不排序先分组，最可能的结果是？"
options = [
  "和排序后一样",
  "组之间出现重复的键",
  "抛 ValueError",
  "结果按字母序自动排列"
]
answer = 1
explain = "groupby 逐个比较相邻元素。数据无序时，同一个键会出现在多个不相邻的位置，于是同一键产生多个分组——先 sorted 再 groupby 是固定套路。"
```

## 小结

- `chain` 串流、`islice` 切无限流、`count/cycle` 无限生成。
- `groupby` 只对**相邻**键分组，先排序。
- `combinations` 无序组合、`permutations` 有序排列、`product` 笛卡尔积。
- 全部惰性：组合使用不会产生中间列表。
