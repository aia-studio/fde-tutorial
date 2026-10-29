+++
id = "s3-64-perf-intuition"
order = 64
stage = "s3"
official_group = "moderate"
title = "性能直觉与 timeit"
concepts = ["timeit", "complexity", "membership", "premature optimization"]
prereq = [62]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：timeit"
url = "https://docs.python.org/3/library/timeit.html"

[[doc_refs]]
title = "PEP 8：编程建议（过早优化）"
url = "https://peps.python.org/pep-0008/#programming-recommendations"
+++

# 先建立量级直觉，再谈优化

优化前必须知道两件事：**量级差在哪**（O(1) 与 O(n)），以及**实测差多少**（timeit）。这一课用数据建立几条直觉，之后写代码时的取舍就有了依据。

## 成员判断：O(n) 与 O(1) 的量级差

```python
import timeit

setup = "data = list(range(10000)); data_set = set(data)"
t_list = timeit.timeit("9999 in data", setup=setup, number=1000)
t_set = timeit.timeit("9999 in data_set", setup=setup, number=1000)
print(t_set < t_list / 10)
```

```expect
True
```

`in list` 要从头扫到尾，`in set` 直接算哈希。10 万元素、查 1000 次的量级下差距是数十倍——这是把 `in some_list` 改成 `in some_set` 的全部理由。注意结论只在**数据量大、判断频繁**时成立：三个元素的列表，先建 set 反而亏。

## 用 timeit 的正确姿势

```python
import timeit

t = timeit.timeit("'-'.join(str(n) for n in range(100))", number=10000)
print(t > 0)
```

```expect
True
```

`timeit` 的三个要点：默认**关闭垃圾回收**（测的是纯执行）、`number` 指定重复次数（总时长除以它）、`setup` 里放准备工作（不计时）。同机多次运行的波动通常在几个百分点内，量级差在个位数百分点内都能视为"相当"。

> [!warn] 避免过早优化
> PEP 8 引用 Knuth：「过早优化是万恶之源」。排序规则是：**先正确，再可读，实测证明慢，最后才优化**——且优化必须用 timeit/profiler 证明有效，而不是"我觉得 set 快"。

## 复杂度速查：常见操作的成本

| 操作 | list | dict / set |
|---|---|---|
| `x in obj` | O(n) | O(1) |
| `obj[i]` | O(1) | O(1) |
| 头部插入 | O(n) | — |
| `append` / `obj[k]=v` | O(1) | O(1) 摊还 |

这张表 + 实测习惯，覆盖日常 90% 的性能决策。更细的（字符串拼接、函数调用开销、PyPy 差异）等 profiler 告诉你，而不是背表。

```quiz
question = "发现程序慢，第一件事应该做什么？"
options = [
  "把循环里的方法调用换成内联代码",
  "用 timeit/profiler 找到真正耗时的位置",
  "把所有容器换成 set",
  "用多线程并行所有循环"
]
answer = 1
explain = "直觉定位慢点通常是错的（常常是 IO 或某一个小函数）。先测量，找到占大头的 20%，再针对性优化——其余代码保持可读。"
```

## 小结

- `in list` O(n)、`in set` O(1)，数据量大且频繁判断时才值得换。
- `timeit` 关 GC、用 `setup` 隔离准备、看多次均值。
- 复杂度表建立直觉，实测确认结论。
- 反对过早优化：正确 → 可读 → 实测慢 → 才优化。
