+++
id = "s3-65-profiling"
order = 65
stage = "s3"
official_group = "moderate"
title = "性能剖析"
concepts = ["cProfile", "pstats", "tracemalloc", "hotspot"]
prereq = [64]
requires_python = "3.15"
allow_network = false
xp = 20

[[doc_refs]]
title = "Library Reference：cProfile 与 pstats"
url = "https://docs.python.org/3/library/profile.html"

[[doc_refs]]
title = "Library Reference：tracemalloc"
url = "https://docs.python.org/3/library/tracemalloc.html"
+++

# profiler 会告诉你真相

timeit 回答"这段代码多快"；profiler 回答"整个程序的时间花在哪"。**没有 profiler 就开始优化，是瞎猜**——直觉找热点，十次九错。

## cProfile：时间花在哪个函数

```python
import cProfile
import pstats
import io


def slow_part():
    return sum(i * i for i in range(20000))


def fast_part():
    return 1 + 1


def main():
    slow_part()
    fast_part()


pr = cProfile.Profile()
pr.enable()
main()
pr.disable()

out = io.StringIO()
pstats.Stats(pr, stream=out).sort_stats("cumulative").print_stats(5)
report = out.getvalue()

print("ncalls" in report)
print("slow_part" in report)
```

```expect
True
True
```

报告里两个关键列：`tottime`（本函数自身耗时，不含子调用）和 `cumtime`（含子调用的累计）。**找优化点看 tottime 排序**——`cumtime` 高的往往只是调用了很多本来就该慢的东西。

## tracemalloc：内存花在哪个对象

```python
import tracemalloc

tracemalloc.start()
data = [bytes(1024) for _ in range(100)]
current, peak = tracemalloc.get_traced_memory()
snapshot = tracemalloc.take_snapshot()
tracemalloc.stop()

print(current >= 100 * 1024)
print(peak >= current)
```

```expect
True
True
```

`current` 是当前占用量（100 个 1KB），`peak` 是历史峰值，`snapshot` 能按文件行号对比两次快照、找出内存增长的来源。排查"程序越跑越占内存"（泄漏）就靠它。

## 剖析的正确流程

```text
1. 用真实数据量跑 cProfile（不是 10 条记录）
2. tottime 排序，找前 3 名
3. 对第一名做最小复现，用 timeit 验证改进
4. 改完必须重测总耗时——局部快了整体没变快=白改
```

> [!warn] 别在剖析模式下优化
> cProfile 会给每个函数调用加计时开销（约 2 倍慢），所以它只回答"谁占大头"，**不能**用它比较两个实现的绝对速度——那是 timeit 的事。两个工具分工明确。

```quiz
question = "cProfile 报告里 `tottime` 和 `cumtime` 的区别是？"
options = [
  "tottime 是自身耗时，cumtime 包含它调用的所有函数",
  "tottime 是平均耗时，cumtime 是总耗时",
  "tottime 是 CPU 时间，cumtime 是墙上时间",
  "两者相同，只是单位不同"
]
answer = 0
explain = "tottime 不含子调用（找「谁在烧 CPU」），cumtime 含全部子调用（看「入口函数整体成本」）。优化热点看 tottime 排序。"
```

## 小结

- `cProfile` 找函数热点，`tottime` 排序是入口。
- `tracemalloc` 查内存增长来源，`peak` 看峰值。
- 剖析用真实数据量；改完必须重测整体。
- 剖析与基准测试分工：找热点用 cProfile，比速度用 timeit。
