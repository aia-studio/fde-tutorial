+++
id = "s3-66-optimization"
order = 66
stage = "s3"
official_group = "moderate"
title = "优化实战：从算法到内置工具"
concepts = ["algorithm", "Counter", "join", "builtin", "optimization"]
prereq = [65]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：timeit"
url = "https://docs.python.org/3/library/timeit.html"

[[doc_refs]]
title = "Library Reference：collections.Counter"
url = "https://docs.python.org/3/library/collections.html#collections.Counter"
+++

# 优化顺序：算法 → 数据结构 → 内置 → 最后才是微优化

这一课演示三层优化的实际收益差多少，并给出"什么时候停手"的判断标准。所有对比都用 `timeit` 实测。

## 第一层：换数据结构（收益最大）

```python
import timeit

items = ["a", "b"] * 5000

manual = "counts = {}\nfor x in items:\n    counts[x] = counts.get(x, 0) + 1"
counter = "Counter(items)"

t_manual = timeit.timeit(manual, globals={"items": items}, number=50)
t_counter = timeit.timeit(counter, globals={"items": items, "Counter": __import__("collections").Counter}, number=50)

print(t_counter < t_manual)
```

```expect
True
```


手写循环 → `Counter`：C 实现的 `_count_elements` 替代了 Python 层循环。这种"换成内置/换数据结构"的优化，通常比微调语句快几倍，且代码更短。

## 第二层：减少 O(n²) 的拼接

```python
import timeit

parts = ["x"] * 5000

t_concat = timeit.timeit(
    "s = ''\nfor p in parts:\n    s = s + p",
    globals={"parts": parts}, number=20
)
t_join = timeit.timeit(
    "''.join(parts)",
    globals={"parts": parts}, number=20
)

print(t_join < t_concat / 10)
```

```expect
True
```

字符串不可变，`s = s + p` 每次都复制整个字符串——循环拼接是 O(n²)。`join` 一次成型，O(n)。这是字符串处理里收益最大的一条规则。

## 第三层：微优化，收益有限

```python
import timeit

setup = "f = str.upper; data = ['a', 'b'] * 1000"
t_method = timeit.timeit("[x.upper() for x in data]", setup=setup, number=100)
t_bound = timeit.timeit("[f(x) for x in data]", setup=setup, number=100)

print(f"方法调用 {t_method:.4f}s，预绑定 {t_bound:.4f}s")
```

把 `x.upper()` 换成预先绑定的 `f(x)` 快一点（省一次属性查找），但差距常在个位数百分比到 30% 之间漂移，甚至可能翻转——所以这块没有预期输出。**只有 profiler 显示这个循环真是热点时才值得做**，否则是给代码可读性上税。

> [!tip] 什么时候停手
> 每层优化后重测整体耗时。出现以下情况立即停：改完的数据没人能看懂、优化点在实测中占比不足 5%、为省 10% 内存引入了新依赖。优化是投入产出比的游戏，不是竞技。

```quiz
question = "字符串循环拼接 `s = s + p` 慢的根本原因是？"
options = [
  "+ 运算符本身慢",
  "字符串不可变，每次拼接都要复制整个新串，O(n²)",
  "解释器无法优化循环",
  "join 是 C 实现所以一定更快"
]
answer = 1
explain = "核心是不可变性带来的复制成本。join 先算总长度一次性分配，是 O(n)。「join 是 C 实现」是顺带的好处，不是根本原因。"
```

## 小结

- 顺序：换算法/数据结构 → 消灭 O(n²) 模式 → 最后微优化。
- 计数用 `Counter`，拼接用 `join`，成员判断用 `set`。
- 每层优化都用 timeit 验证，并重测整体耗时。
- 占比不足 5% 的热点不值得优化。
