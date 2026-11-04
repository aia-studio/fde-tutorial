+++
id = "s2-44-collections"
order = 44
stage = "s2"
official_group = "moderate"
title = "collections"
concepts = ["Counter", "defaultdict", "deque", "namedtuple", "OrderedDict"]
prereq = [42]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：collections"
url = "https://docs.python.org/3/library/collections.html"

[[doc_refs]]
title = "Library Reference：deque"
url = "https://docs.python.org/3/library/collections.html#deque-objects"
+++

# 四个容器，替代大半手写循环

`Counter` / `defaultdict` / `deque` / `namedtuple` 都是内置容器的**专用强化版**。该用哪个，取决于你想省掉哪段代码。

## Counter：数数

```python
from collections import Counter

words = ["a", "b", "a", "c", "a"]
counts = Counter(words)

print(counts)
print(counts.most_common(1))
print(counts["b"], counts["不存在的键"])
```

```expect
Counter({'a': 3, 'b': 1, 'c': 1})
[('a', 3)]
1 0
```

对比第 9 课手写的 `counts.get(w, 0) + 1` 循环——`Counter` 一行完成，还自带 `most_common` 排名。缺键返回 0 而不抛错，这是它对"数数"场景的特化。

## defaultdict：缺键自动补

```python
from collections import defaultdict

groups = defaultdict(list)
for word in ["ab", "ba", "cc", "ac"]:
    groups[word[0]].append(word)

print(dict(groups))
```

```expect
{'a': ['ab', 'ac'], 'b': ['ba'], 'c': ['cc']}
```

访问不存在的键时调用 `default_factory` 造一个默认值（这里是空列表）。比 `setdefault` 或 `get` 检查干净——**逻辑里不再出现"键在不在"的判断**。

> [!warn] defaultdict 的副作用
> 之后任何**读取**不存在键的操作都会悄悄创建空条目（比如 `if "x" in groups` 没事，但 `groups["x"]` 就会加进 dict）。需要严格语义时用 `dict(d)` 收敛。

## deque：两端操作 O(1)

```python
from collections import deque

q = deque([1, 2, 3], maxlen=3)
q.append(4)
print(q)

q.appendleft(0)
print(list(q))
```

```expect
deque([2, 3, 4], maxlen=3)
[0, 2, 3]
```

列表的 `insert(0, x)` 是 O(n)（要整体挪动），`deque` 的两端操作是 O(1)。队列、滑动窗口、最近 N 条记录都该用它。`maxlen=3` 自动丢弃超出的旧元素——"最近记录"场景直接白送。

## namedtuple：轻量记录

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)

print(p.x, p.y)
print(p._asdict())
```

```expect
3 4
{'x': 3, 'y': 4}
```

比元组可读（`p.x` vs `p[0]`），比 dataclass 轻（不可变、无方法生成）。现代写法也可以用 `typing.NamedTuple` 或 `@dataclass`，看项目风格。

```quiz
question = "需要在开头频繁插入元素，用列表 `insert(0, x)` 还是 deque？为什么？"
options = [
  "列表，insert 语法更简单",
  "deque，两端操作 O(1)，列表 insert(0) 要整体移动 O(n)",
  "无所谓，复杂度一样",
  "用 set，去重顺便排序"
]
answer = 1
explain = "列表底层是连续数组，头部插入要挪动所有元素。deque 是双向链表块结构，appendleft/popleft 都是 O(1)。数据量大时差距是数量级的。"
```

## 小结

- `Counter` 计数与排名，缺键返回 0。
- `defaultdict` 消灭"键在不在"的检查，注意读取也会创建条目。
- `deque` 两端 O(1)，`maxlen` 自动滑窗。
- `namedtuple` 是可读的轻量记录；重一点的用 dataclass。
